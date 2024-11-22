#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import timedelta, time
import logging

from google.appengine.ext import db
from google.appengine.api import users
from utils.decorators import login_required
from utils.bseu_schedule import fetch_and_parse_week
from utils.helpers import _flash

from auth import get_user_credentials_from_session

from flask import Blueprint, redirect, abort

from models import Student

from googleapiclient.discovery import build

DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S.000Z'

import_handlers = Blueprint('import_handlers', __name__)

def insert_event(calendar_service, schedule_event, user_calendar='primary'):
    event = {}
    event['summary'] = schedule_event.title or 'bseu-api event'
    event['description'] = schedule_event.description or 'study hard'
    event['location'] = schedule_event.location or 'in space'

    start_time = schedule_event.starttime
    end_time = schedule_event.endtime

    # start_time: datetime.datetime(2023, 9, 25, 16, 5) | None
    if start_time is None:
        # Use current time for the start_time and have the event last 1 hour
        start_time = time.strftime(DATETIME_FORMAT, time.gmtime())
        end_time = time.strftime(DATETIME_FORMAT, time.gmtime(time.time() + 3600))
    else:
        start_time = (start_time - timedelta(hours=3)).strftime(DATETIME_FORMAT)
        end_time = (end_time - timedelta(hours=3)).strftime(DATETIME_FORMAT)

    # start_time: '2023-09-25T13:05:00.000Z'
    event['start'] = {'dateTime': start_time}
    event['end'] = {'dateTime': end_time}

    try:
        # Events#insert API ref: https://developers.google.com/calendar/api/v3/reference/events/insert
        calendar_service.events().insert(calendarId=user_calendar, body=event).execute()
    except Exception as e:
        logging.error('import was unsuccessful - skipping: %s' % e)
        # _flash(u'Не удалось импортировать расписание.')
        abort(403) # assume it's a 403 for now, abort on 1st failed insert
    else:
        logging.debug('import was successful: %s-%s' % (event['summary'], event['description']))


def create_calendar_events(user, credentials, event_list):
    if credentials is None:
        logging.info('[create_calendar_events] no credentials provided for user %s - skipping' % user.student.email())
        return

    # https://developers.google.com/identity/protocols/oauth2/web-server#callinganapi
    # After obtaining an access token, your application can use that token to authorize API requests on behalf of a given user account.
    # Use the user-specific authorization credentials to build a service object for the API that you want to call,
    # and then use that object to make authorized API requests.
    calendar_service = build('calendar', 'v3', credentials=credentials, cache_discovery=False)
    for event in event_list:
        insert_event(calendar_service, event, user.calendar_id)


@import_handlers.route('/import')
@login_required
def import_events():
    user = Student.all().filter("student =", users.get_current_user()).order("-lastrun").get()
    credentials = get_user_credentials_from_session(user)
    create_calendar_events(user, credentials, fetch_and_parse_week(user))
    _flash(u'Расписание успешно добавлено в календарь!')
    return redirect('/')
