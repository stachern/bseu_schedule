#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import timedelta, time
import logging

from google.appengine.ext import db
from google.appengine.api import users
from webapp2_extras.appengine.users import login_required
from utils.bseu_schedule import fetch_and_parse_week

from handler import RequestHandler
from gaesessions import get_current_session
from models import Student, Event
import models
from settings import API_APP
import gdata.gauth
import gdata.calendar.data
import gdata.calendar.client
import atom.data
from utils import mailer, bseu_schedule


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


def create_calendar_events(user, event_list):
    access_token_key = 'access_token_%s' % user.student.user_id()
    gcal_client.auth_token = gdata.gauth.ae_load(access_token_key)
    for event in event_list:
        InsertSingleEvent(gcal_client, event.title, event.description, event.location, event.starttime, event.endtime,
                          user.calendar_id)


class ImportHandler(RequestHandler):
    @login_required
    def get(self):
        user = Student.all().filter("student =", users.get_current_user()).order("-lastrun").get()
        create_calendar_events(user, bseu_schedule.fetch_and_parse_week(user))
        self.session = get_current_session()
        self.session['messages'] = ["Импорт успешен!"]
        self.redirect('/')


class BatchInserter(RequestHandler):
    def get(self):
        logging.info('starting batch insert job')
        users = Student.all().filter("auto =", True).order("-lastrun").fetch(limit=1000)
        for user in users:
            if user.calendar_id:
                try:
                    event_list = bseu_schedule.fetch_and_parse_week(user)
                except Exception, e:
                    logging.error(e)
                else:
                    if event_list:
                        create_calendar_events(user, event_list)
                        mailer.send(recipient=user.student.email(), params={'user': user.student, 'events': event_list})
        self.response.out.write('success')