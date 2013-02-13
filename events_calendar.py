#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import timedelta, time
import urllib
import logging

from google.appengine.ext import db
from google.appengine.api import urlfetch, users
from webapp2_extras.appengine.users import login_required

from handler import RequestHandler
from gaesessions import get_current_session
from models import Student, Event
from settings import BSEU_SHEDULE_URL, HEADERS, API_APP, BSEU_DEFAULT_PERIOD, ACTION_ID
import gdata.gauth
import gdata.calendar.data
import gdata.calendar.client
import atom.data
import schedule_parser
import mailer


gcal_client = gdata.calendar.client.CalendarClient(source=API_APP['APP_NAME'])


def InsertSingleEvent(calendar_client, title='bseu-api event',
                      content='study hard', where='in space',
                      start_time=None, end_time=None, ucalendar=None):
    event = gdata.calendar.data.CalendarEventEntry()
    event.title = atom.data.Title(text=title)
    event.content = atom.data.Content(text=content)
    event.where.append(gdata.calendar.data.CalendarWhere(value=where))

    if start_time is None:
        # Use current time for the start_time and have the event last 1 hour
        start_time = time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime())
        end_time = time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime(time.time() + 3600))
    else:
        start_time = (start_time - timedelta(hours=3)).strftime('%Y-%m-%dT%H:%M:%S.000Z')
        end_time = (end_time - timedelta(hours=3)).strftime('%Y-%m-%dT%H:%M:%S.000Z')

    event.when.append(gdata.calendar.data.When(start=start_time, end=end_time))

    try:
        if ucalendar is None:
            calendar_client.InsertEvent(event)
        else:
            calendar_client.InsertEvent(event, ucalendar)
    except Exception, e:
        logging.error('import was unsuccessful - skipping: %s' % e)
    else:
        logging.debug('import was successful: %s-%s' % (title, content))


def create_calendar_events(who):
    access_token_key = 'access_token_%s' % who.student.user_id()
    gcal_client.auth_token = gdata.gauth.ae_load(access_token_key)
    results = Event.all().filter("creator =", who.student).order("starttime").fetch(limit=30)
    batch = []
    for event in results:
        InsertSingleEvent(gcal_client, event.title, event.description, event.location, event.starttime, event.endtime,
                          who.calendar_id)
        batch.append(event)
    db.delete(batch)


def fetch(student):
    data = {
        '__act': ACTION_ID,
        'period': BSEU_DEFAULT_PERIOD,
        'faculty': student.faculty,
        'group': student.group,
        'course': student.course,
        'form': student.form
    }

    result = urlfetch.fetch(url=BSEU_SHEDULE_URL,
                            payload=urllib.urlencode(data),
                            method=urlfetch.POST,
                            headers=HEADERS)
    try:
        parsed_list = schedule_parser.read(result.content)
    except Exception, e:
        logging.error(e)
    else:
        for parsed in parsed_list:
            new_schedule = Event(title=parsed['subject'],
                                 description=parsed['description'],
                                 location=parsed['location'],
                                 starttime=parsed['date']['start'],
                                 endtime=parsed['date']['end'],
                                 creator=student.student)
            new_schedule.put()


class ImportHandler(RequestHandler):
    @login_required
    def get(self):
        user_settings = Student.all().filter("student =", users.get_current_user()).order("-lastrun").get()
        create_calendar_events(user_settings)
        self.session = get_current_session()
        self.session['import'] = True
        self.redirect('/')


class BatchFetcher(RequestHandler):
    def get(self):
        logging.info('starting batch fetch job')
        results = Student.all().filter("auto =", True).order("-lastrun").fetch(limit=1000)
        for stud in results:
            if stud.calendar:
                logging.info('fetching for %s' % stud.student.email())
                fetch(stud)
        self.response.out.write('success')


class BatchInserter(RequestHandler):
    def get(self):
        logging.info('starting batch insert job')
        results = Student.all().filter("auto =", True).order("-lastrun").fetch(limit=1000)
        for stud in results:
            if stud.calendar:
                create_calendar_events(stud)
                mailer.send(recipient=stud.student.email(), params={'user': stud.student})
        self.response.out.write('success')