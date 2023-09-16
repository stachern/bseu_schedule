import os
import urllib
from google.appengine.api import urlfetch
from models import Event
import settings
from utils import schedule_parser
from utils.decorators import cached
from google.appengine.ext.webapp import template  # TODO: Change!


@cached(time=360)
def _fetch_raw_html_schedule(faculty, course, group, form, period=settings.BSEU_WEEK_PERIOD):
    data = {
        '__act': settings.ACTION_ID,
        'period': period,
        'faculty': faculty,
        'group': group,
        'course': course,
        'form': form
    }

    return urlfetch.fetch(url=settings.BSEU_SCHEDULE_URL,
                          payload=urllib.urlencode(data),
                          method=urlfetch.POST,
                          headers=settings.HEADERS).content


def fetch_and_show_week(student):
    try:
        return schedule_parser.show(_fetch_raw_html_schedule(student.faculty, student.course, student.group,
                                                             student.form)
        ).replace('id="sched"', 'class="table table-bordered table-hover"')
    except IndexError:
        return template.render(os.path.join(settings.ROOT_PATH, 'templates/html/misc/no_schedule_alert.html'), {})


def fetch_and_show_semester(student):
    try:
        return schedule_parser.show(
            _fetch_raw_html_schedule(student.faculty, student.course, student.group,
                                     student.form, settings.BSEU_SEMESTER_PERIOD)
        ).replace('id="sched"', 'class="table table-bordered table-hover"')
    except IndexError:
        return template.render(os.path.join(settings.ROOT_PATH, 'templates/html/misc/no_schedule_alert.html'), {})


def fetch_and_parse_week(student):
    events = schedule_parser.read(_fetch_raw_html_schedule(student.faculty, student.course, student.group,
                                                           student.form))
    return [Event(title=event['subject'],
                  description=event['description'],
                  location=event['location'],
                  starttime=event['date']['start'],
                  endtime=event['date']['end'],
                  creator=student.student) for event in events]


