import json
import os
from urllib.parse import urlparse

from flask import render_template, Response
import redis

from app import app


MAPS_API_KEY = os.environ["MAPS_API_KEY"]

url = urlparse(os.environ.get('REDISCLOUD_URL'))
redis_client = redis.Redis(host=url.hostname, port=url.port, password=url.password)


@app.route('/')
def home_route():
    """ Serves the / route. """
    return render_template('index.html', maps_api_key=MAPS_API_KEY)


@app.route('/covid')
def covid_route():
    """ Serves the /covid route. """
    return render_template('covid.html', maps_api_key=MAPS_API_KEY)


@app.route('/events')
def events_route():
    """
    Returns a JSON of all events on the Perilous Chronicle website,
    partitioned by month-year.
    """
    return Response(
        json.loads(redis_client.get('events:all')),
        mimetype="application/json"
    )


@app.route('/covid_events')
def covid_events_route():
    """
    Returns a JSON of all events tagged "COVID-19 Crisis" on the Perilous
    Chronicle website.
    """
    return Response(
        json.loads(redis_client.get('events:covid')),
        mimetype="application/json"
    )
