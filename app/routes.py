from datetime import datetime, timedelta
from functools import lru_cache
import itertools
import json
import os
import re
import time

from dateutil.parser import parse
from flask import render_template, Response
import requests

from app import app

LOCATION_QUERY_API = 'http://dev.virtualearth.net/REST/v1/Locations/%s?maxResults=1&key=%s'
PC_URL = 'https://perilouschronicle.com/wp-json/wp/v2/posts?per_page=%s&page=%s'

MAPS_API_KEY = os.environ["MAPS_API_KEY"]
RESULTS_PER_PAGE = 100
SESSION = requests.Session()

@app.before_first_request
def initialize():
    events_route()


@app.route('/')
def home_route():
    return render_template('index.html', maps_api_key=MAPS_API_KEY)


@app.route('/events')
def events_route():
    # It's probably not worth optimizing this too much, given Heroku will
    # put the instance to sleep after 30 min. Obviously this would be much
    # better as a background task but that's a hassle to set up in Heroku.
    return Response(get_events(get_ttl_hash(60 * 60 * 24)), mimetype="application/json")


@lru_cache(maxsize=1)
def get_events(ttl_hash):
    """
    Retrieves the events grouped by month-year.
    :param ttl_hash: A hash from get_ttl_hash() to evict the cached events
    :return: A list of dicts for each month-year in the time range,
             each containing a list of events in that month-year
    """
    del ttl_hash
    posts = sorted(get_posts(), key=get_post_myear)
    events_by_myear = [{'myear': myear, 'events': list(events)}
                       for myear, events in itertools.groupby(posts, get_post_myear)]

    # Fill in empty months
    empty_months = [{'myear': m, 'events': []}
                    for m in get_myears_without_events(events_by_myear, posts)]
    result = sorted(events_by_myear + empty_months, key=get_post_myear)

    return json.dumps(result)


def get_ttl_hash(seconds):
    """
    Computes a different hash every `seconds`. Changing the function parameter
    passed to the LRU is functionally equivalent to evicting the cache key.
    :param seconds: The frequency
    """
    return round(time.time() / seconds)


def get_post_myear(post):
    return post['myear']


def get_posts():
    """
    Returns the list of WordPress posts from the Perilous Chronicle site.
    :return: A list of dicts containing the keys date, location, link, myear, and title
    """
    page = 1
    posts = []
    while True:
        resp = SESSION.get(PC_URL % (RESULTS_PER_PAGE, page))
        if resp.status_code != 200:
            break

        for obj in resp.json():
            posts.append({
                'date': obj['date'],
                'location': parse_location(obj['content']['rendered'], obj['title']['rendered']),
                'link': obj['link'],
                'myear': parse(obj['date']).strftime('%Y%m'),
                'title': obj['title']['rendered']
            })

        page += 1

    return posts


def get_myears_without_events(events_by_myear, posts):
    """
    Computes the month-years which have no events.
    :param events_by_myear: A list with events grouped by myear
    :param posts: The list of posts
    :return: A list of month-year strings, e.g. '201808'
    """
    first_month = datetime.strptime(events_by_myear[0]['myear'], '%Y%m')
    last_month = datetime.strptime(events_by_myear[-1]['myear'], '%Y%m')
    all_months = list(set(
        (first_month + timedelta(_)).strftime('%Y%m')
        for _ in range((last_month - first_month).days)
    ))
    myears_with_events = set(post['myear'] for post in posts)
    return [m for m in all_months if m not in myears_with_events]


def parse_location(content, title):
    """
    Scrapes the location from a post.
    :param content: The body of the post
    :param title: The title of the post
    :return: The [lat, lng] coordinates tuple of the post
    """
    # Hi... yea.... scraping content isn't fun
    body = content.replace('\n', '')
    body = re.sub(r'(?:<p>)?<!-- /?wp:paragraph -->(?:</p>)?', '', body)
    body = re.sub(r'(?:<p>)?<!-- /?wp:image .*?-->(?:</p>)?', '', body)

    # Some posts are formatted slightly differently
    try:
        location = re.findall(r'^(?:<p.*?>)?(.*?)<(?:br|/p)', body)[0]
    except IndexError:
        location = re.findall(r'^\r*(.*?)\r', body)[0]

    # Heuristic to see if parsed location is bad; if so, try parsing title
    if location.count(' ') > 10:
        location = title
        location = re.sub(r'^.*? at ', '', location)
        location = re.sub(r'^.*? to ', '', location)
        print("Parsed title [%s] to [%s]." % (title, location))

    location = re.sub(r'<.*?>', '', location)
    location = location.replace('&#8217;', '\'')
    location = location.replace(u'\xa0', u' ')
    location = location.replace('&#8211', '–')

    # Special case for National Prison Strike posts
    location = re.sub(r'\d+ National Prison Strike: ', '', location)

    return query_location(location, title)


@lru_cache(maxsize=500)
def query_location(location, title):
    """
    Returns the lat/lng coordinates for a specified location.
    :param location: The location to look up
    :param title: The title of the post being looked up
    :return: A tuple of [lat, lng]
    """
    resp = SESSION.get(LOCATION_QUERY_API % (location, MAPS_API_KEY))
    try:
        return resp.json()["resourceSets"][0]["resources"][0]["point"]["coordinates"]
    except (json.decoder.JSONDecodeError, IndexError):
        # Sometimes we can't parse out a location for a post. Skip it if so
        print("Failed to retrieve coordinates for %s. Setting to 0,0" % title)
        return [0, 0]
