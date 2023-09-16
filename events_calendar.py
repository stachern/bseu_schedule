#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import timedelta, time
import logging

from google.appengine.ext import db
from google.appengine.api import users
from utils.decorators import login_required
from utils.bseu_schedule import fetch_and_parse_week

from flask import Blueprint, redirect

from gaesessions import get_current_session
from models import Student, Event
import models
from settings import API_APP
import gdata.gauth
import gdata.calendar.data
import gdata.calendar.client
import atom.data
from utils import mailer, bseu_schedule

import_handlers = Blueprint('import_handlers', __name__)

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

# FYI: Not even working in production
@import_handlers.route('/import')
@login_required
def import_events():
    user = Student.all().filter("student =", users.get_current_user()).order("-lastrun").get()
    create_calendar_events(user, bseu_schedule.fetch_and_parse_week(user))
    self.session = get_current_session()
    self.session['messages'] = ["Импорт успешен!"]
    return redirect('/')
