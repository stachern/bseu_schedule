from urllib.parse import urlencode
from datetime import datetime, timedelta
from pytz import timezone
import logging

import requests
from flask import render_template
from models import Event
import settings
from utils import schedule_parser
from utils.decorators import cached


def _seconds_till_around_midnight():
    tz = timezone("Europe/Minsk")
    midnight = (datetime.now(tz) + timedelta(days=1)).replace(hour=0, minute=2, microsecond=0, second=0)
    return (midnight - datetime.now(tz)).seconds

def cache_time():
    """ Cache time should be seconds till 00:02am next day or at least 6min """
    return max(_seconds_till_around_midnight(), 360)


@cached(time=cache_time())
def _fetch_raw_html_schedule(faculty, course, group, form, period=settings.BSEU_WEEK_PERIOD):
    """ Fetches raw HTML schedule from the BSEU schedule.
    Shows the cached schedule most of the time so we don't hit university schedule frequently.
    This also enables us to show the schedule even when the BSEU schedule is down.
    Drops the cache at 00:02am daily. """

    data = {
        '__act': settings.ACTION_ID,
        'period': period,
        'faculty': faculty,
        'group': group,
        'course': course,
        'form': form
    }

    return requests.post(settings.BSEU_SCHEDULE_URL,
                         data=urlencode(data),
                         headers=settings.HEADERS).content


def _fetch_and_show_period(student, period):
    try:
        return schedule_parser.show(
            _fetch_raw_html_schedule(student.faculty, student.course, student.group, student.form,
                                     period)
        ).replace('id="sched"', 'class="table table-bordered table-hover"')
    except IndexError:
        return render_template('html/misc/no_schedule_alert.html')
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
        # This handles the 500 error when bseu.by is down!
        caller_fn = 'fetch_and_show_week' if period == settings.BSEU_WEEK_PERIOD else 'fetch_and_show_semester'
        url = settings.BSEU_SCHEDULE_URL
        logging.exception(f'[{caller_fn}] {url} is currently unresponsive: {e}')
        return render_template('html/misc/schedule_down_alert.html')


def fetch_and_show_week(student):
    return _fetch_and_show_period(student, settings.BSEU_WEEK_PERIOD)


def fetch_and_show_semester(student):
    return _fetch_and_show_period(student, settings.BSEU_SEMESTER_PERIOD)


def fetch_and_parse_week(student):
    events = schedule_parser.read(_fetch_raw_html_schedule(student.faculty, student.course, student.group,
                                                           student.form))
    return [Event(title=event['subject'],
                  description=event['description'],
                  location=event['location'],
                  starttime=event['date']['start'],
                  endtime=event['date']['end']) for event in events]
