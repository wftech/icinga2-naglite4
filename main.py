import os
import datetime

from flask import Flask, render_template
from flask_humanize import Humanize
from jinja2 import StrictUndefined
from requests.exceptions import RequestException

from helpers import State, StateCssClass
from models import MonitoringStatus
from icinga2api.client import Client as Icinga2Client

app = Flask(__name__, static_url_path='/naglite4/static', static_folder='static')
app.jinja_env.undefined = StrictUndefined
humanize = Humanize(app)
icinga2api = Icinga2Client(config_file='icinga2-api.ini')

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
REFRESH = os.getenv('REFRESH', 15)


@app.template_filter('icinga_status')
def status_filter(check_result):
    if check_result is None:
        return 'N/A'
    try:
        return State(int(check_result['state'])).name
    except ValueError:
        return 'N/A'


@app.template_filter('icinga_status_css_class')
def status_css_class_filter(check_result):
    if check_result is None:
        return ''
    try:
        return getattr(StateCssClass, State(int(check_result['state'])).name).value
    except ValueError:
        return ''


@app.route('/')
def view_index():
    try:
        context = dict(
            monitoring=MonitoringStatus(apiclient=icinga2api),
            current_time=datetime.datetime.now().isoformat(sep=' ', timespec='seconds')
        )
        body = render_template('index.html', **context)
    except RequestException as e:
        import sys
        sys.stderr.write(str(e))

        context = dict(
            current_time=datetime.datetime.now().isoformat(sep=' ', timespec='seconds')
        )
        body = render_template('api_error.html', **context)
        headers = dict(
            Refresh='5'
        )
        return (body, 200, headers)
    headers = dict(
        Refresh='{}'.format(REFRESH)
    )
    return (body, 200, headers)


if __name__ == '__main__':
    import sys

    sys.stderr.write("# This should be run using UWSGI container or `flask run` \n")
    sys.stderr.write("# FLASK_APP=main FLASK_DEBUG=1 pipenv run flask run \n")
    raise ValueError("Invalid invocation")
