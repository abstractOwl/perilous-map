import itertools
import json
import os
import re
import requests

from datetime import datetime, timedelta
from dateutil.parser import parse
from flask import Flask, render_template

EVENTS_CACHE_KEY = 'events'
PC_URL = 'https://perilouschronicle.com/wp-json/wp/v2/posts?per_page=%s&page=%s'
LOCATION_QUERY_API = 'http://dev.virtualearth.net/REST/v1/Locations/%s?maxResults=1&key=%s'
RESULTS_PER_PAGE = 100
MAPS_API_KEY = os.environ["MAPS_API_KEY"]

app = Flask(__name__, static_url_path='/static')
cache = dict()

@app.route('/')
def home_route():
    return render_template('index.html', maps_api_key=MAPS_API_KEY)

@app.route('/events')
def events_route():
    # It's probably not worth optimizing this too much, given Heroku will
    # put the instance to sleep after 30 min
    if EVENTS_CACHE_KEY in cache:
        return cache[EVENTS_CACHE_KEY]
    cache[EVENTS_CACHE_KEY] = get_events()
    return cache[EVENTS_CACHE_KEY]

def get_events():
    sort_by_myear = lambda post: post['myear']

    posts = sorted(get_posts(), key=sort_by_myear)
    events_by_myear = [{'myear': myear, 'events': list(events)}
                       for myear, events in itertools.groupby(posts, sort_by_myear)]

    # Fill in empty months
    empty_months = [{'myear': m, 'events': []}
                    for m in get_myears_without_events(events_by_myear, posts)]
    result = sorted(events_by_myear + empty_months, key=sort_by_myear)

    return json.dumps(result)

def get_posts():
    page = 1
    posts = []
    while True:
        resp = requests.get(PC_URL % (RESULTS_PER_PAGE, page))
        if resp.status_code != 200:
            break

        for obj in resp.json():
            posts.append({
                'date': obj['date'],
                'location': parse_location(obj['content']['rendered'], obj['title']),
                'link': obj['link'],
                'myear': parse(obj['date']).strftime('%Y%m'),
                'title': obj['title']['rendered']
            })

        page += 1

    return posts

def get_myears_without_events(events_by_myear, posts):
    first_month = datetime.strptime(events_by_myear[-1]['myear'], '%Y%m')
    last_month = datetime.strptime(events_by_myear[0]['myear'], '%Y%m')
    all_months = list(set(
        (first_month + timedelta(_)).strftime('%Y%m')
        for _ in range((last_month - first_month).days)
    ))
    myears_with_events = set(post['myear'] for post in posts)
    return [m for m in all_months if not m in myears_with_events]

def parse_location(content, title):
    # Hi... yea.... scraping content isn't fun
    body = content.replace('\n', '')
    body = re.sub(r'(?:<p>)?<!-- /?wp:paragraph -->(?:</p>)?', '', body)
    location = re.findall(r'^(?:<p.*?>)?(.*?)<(?:br|/p)', body)[0]
    location = re.sub(r'<.*?>', '', location)
    location = location.replace('&#8217;', '\'').replace(u'\xa0', u' ')

    resp = requests.get(LOCATION_QUERY_API % (location, MAPS_API_KEY))
    try:
        return resp.json()["resourceSets"][0]["resources"][0]["point"]["coordinates"]
    except json.decoder.JSONDecodeError:
        # Sometimes we can't parse out a location for a post. Skip it if so
        print("Failed to retrieve coordinates for %s, setting to 0,0" % title)
        return [0, 0]
