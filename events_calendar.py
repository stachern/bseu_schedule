#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import timedelta, time
import logging

from google.appengine.ext import db
from google.appengine.api import users
from utils.decorators import login_required
from utils.bseu_schedule import fetch_and_parse_week
from utils.helpers import _flash
from utils.ae_helpers import ae_save

from flask import Blueprint, redirect, abort

from gaesessions import get_current_session
from models import Student

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from settings import OAUTH2_SCOPES

DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S.000Z'

import_handlers = Blueprint('import_handlers', __name__)


def insert_event(calendar_service, title='bseu-api event',
                      description='study hard', location='in space',
                      start_time=None, end_time=None, user_calendar='primary'):
    event = {}
    event['summary'] = title
    event['description'] = description
    event['location'] = location

    # start_time: datetime.datetime(2023, 9, 25, 16, 5)
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
        logging.debug('import was successful: %s-%s' % (title, description))


def create_calendar_events(user, event_list):
    session = get_current_session()

    if not 'credentials' in session:
        return redirect('/auth')

    # Store user's access and refresh tokens in the App Engine datastore.
    # FYI: TEMPORARY SOLUTION!
    # TODO: Remove once all users' refresh and access tokens are in the datastore!
    user_id = user.student.user_id()
    refresh_token = session['credentials'].get('refresh_token')
    if refresh_token is not None:
        refresh_token_key = 'refresh_token_%s' % user_id
        ae_save(refresh_token, refresh_token_key)
    access_token = session['credentials'].get('token')
    if access_token is not None:
        access_token_key = 'access_token_%s' % user_id
        ae_save(access_token, access_token_key)

    # https://developers.google.com/identity/protocols/oauth2/web-server#example
    # Load user credentials from the session stored in App Engine datastore
    credentials = Credentials(**session['credentials'])

    # https://developers.google.com/identity/protocols/oauth2/web-server#callinganapi
    # After obtaining an access token, your application can use that token to authorize API requests on behalf of a given user account.
    # Use the user-specific authorization credentials to build a service object for the API that you want to call,
    # and then use that object to make authorized API requests.
    calendar_service = build('calendar', 'v3', credentials=credentials, cache_discovery=False)
    for event in event_list:
        insert_event(calendar_service, event.title, event.description, event.location, event.starttime, event.endtime,
                        user.calendar_id)


@import_handlers.route('/import')
@login_required
def import_events():
    user = Student.all().filter("student =", users.get_current_user()).order("-lastrun").get()
    create_calendar_events(user, fetch_and_parse_week(user))
    _flash(u'Расписание успешно добавлено в календарь!')
    return redirect('/')
