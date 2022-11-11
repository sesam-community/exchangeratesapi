
from flask import Flask, request, Response
from datetime import datetime
from dateutil.relativedelta import relativedelta
import os

import json
import pytz
import iso8601
import requests
import logging

app = Flask(__name__)

logger = None

base_url = "http://api.exchangeratesapi.io/"

def datetime_format(dt):
    return '%04d' % dt.year + dt.strftime("-%m-%dT%H:%M:%SZ")


def to_transit_datetime(dt_int):
    return "~t" + datetime_format(dt_int)


def get_var(var, default = None):
    envvar = default
    if var.upper() in os.environ:
        envvar = os.environ[var.upper()]
    elif request:
        envvar = request.args.get(var)
    logger.debug("Setting %s = %s" % (var, envvar))
    return envvar


@app.route('/', methods=['GET'])
def get_entities():
    since = get_var('since') or "1999-01-04"
    bases = get_var('base') or "EUR" # or "EUR USD" if you want multiple bases
    symbols = get_var('symbols') or ""
    accesskey = get_var('accesskey') or ""


    entities = []

    end = datetime.now(pytz.UTC).date()  # we need to use UTC as salesforce API requires this


    start = iso8601.parse_date(since).date()

    while start <= datetime.now(pytz.UTC).date():
        for base in bases.split():
          logger.debug("GET: %s%s?access_key=XXX&base=%s&symbols=%s" % (base_url, start, base, symbols))
          response = requests.get("%s%s?access_key=%s&base=%s&symbols=%s" % (base_url, start, accesskey, base, symbols))
          result = response.json()
          logger.info("Result = %s" % (result))
          result.update({"_id": "%s-%s" % (base, start)})
          result.update({"_updated": "%s" % start})
          result.update({"date": "%s" % to_transit_datetime(iso8601.parse_date(result["date"]))})
          entities.append(result)

        start = (start + relativedelta(days=1))

    return Response(json.dumps(entities), mimetype='application/json')



if __name__ == '__main__':
    # Set up logging
    format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logger = logging.getLogger('openrates-microservice')

    # Log to stdout
    stdout_handler = logging.StreamHandler()
    stdout_handler.setFormatter(logging.Formatter(format_string))
    logger.addHandler(stdout_handler)

    logger.setLevel(logging.INFO)

    app.run(debug=False, host='0.0.0.0', port=5000)

