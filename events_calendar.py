#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import timedelta, time
import logging

from google.appengine.ext import db
from google.appengine.api import users

from utils import mailer
from utils.decorators import login_required
from utils.bseu_schedule import fetch_and_parse_week
from utils.helpers import _flash

from auth import get_user_credentials_from_session, get_user_credentials_from_ae_datastore

from flask import Blueprint, render_template, redirect, request, abort

from models import Student

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.exceptions import RefreshError

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


def build_calendar_service(user, credentials):
    # Temporary user credentials debugging.
    logging.debug(f'[build_calendar_service] user: {user.student.email()}')

    if credentials.refresh_token is None:
        logging.debug('[build_calendar_service] no credentials.refresh_token for user')

    logging.debug(f'[build_calendar_service] credentials.expired: {credentials.expired}')
    logging.debug(f'[build_calendar_service] credentials.valid: {credentials.valid}')

    # https://developers.google.com/identity/protocols/oauth2/web-server#callinganapi
    # After obtaining an access token, your application can use that token to authorize API requests on behalf of a given user account.
    # Use the user-specific authorization credentials to build a service object for the API that you want to call,
    # and then use that object to make authorized API requests.
    return build('calendar', 'v3', credentials=credentials, cache_discovery=False)


def check_calendar_exists(calendar_service, user_calendar):
    try:
        # Attempt to retrieve the calendar's metadata
        calendar_service.calendarList().get(calendarId=user_calendar).execute()
        return True
    except HttpError as e:
        if e.resp.status == 404:
            return False
        else:
            raise e


def create_calendar_events(user, calendar_service, event_list):
    for event in event_list:
        insert_event(calendar_service, event, user.calendar_id)


@import_handlers.route('/import')
@login_required
def import_events():
    user = Student.all().filter("student =", users.get_current_user()).order("-lastrun").get()
    credentials = get_user_credentials_from_session(user)
    if not credentials:
        # FYI: Reproducible by visiting /clear first and then /import.
        _flash(u'Не удалось импортировать расписание. Повторите попытку еще раз')
        return redirect('/auth')

    calendar_service = build_calendar_service(user, credentials)
    try:
        calendar_exists = check_calendar_exists(calendar_service, user.calendar_id)
    except RefreshError as e:
        # credentials.refresh_token is None
        # URL being requested: GET https://www.googleapis.com/calendar/v3/users/me/calendarList/{calendarId}?alt=json
        # Refreshing credentials due to a 401 response. Attempt 1/2.
        # Exception on /import [GET]
        # google.auth.exceptions.RefreshError: The credentials do not contain the necessary fields need to refresh the access token. You must specify refresh_token, token_uri, client_id, and client_secret.
        #   https://google-auth.readthedocs.io/en/stable/reference/google.oauth2.credentials.html#google.oauth2.credentials.Credentials.refresh
        # Credentials object expired?
        #   https://google-auth.readthedocs.io/en/stable/reference/google.oauth2.credentials.html#google.oauth2.credentials.Credentials.expired
        #   https://google-auth.readthedocs.io/en/stable/reference/google.oauth2.credentials.html#google.oauth2.credentials.Credentials.valid
        logging.error(f'import was unsuccessful: credentials could not be refreshed for user {user.student.email()}')
        _flash(u'Не удалось импортировать расписание. Повторите попытку еще раз')
        return redirect('/auth')
    else:
        if not calendar_exists:
            logging.error(f'import was unsuccessful: non-existing calendar_id for user {user.student.email()}')
            _flash(u'Не удалось импортировать расписание. Выбранный календарь не найден!')
            return redirect('/')

    create_calendar_events(user, calendar_service, fetch_and_parse_week(user))
    _flash(u'Расписание успешно добавлено в календарь!')
    return redirect('/')


@import_handlers.post('/auto-import')
def auto_import_calendar_events():
    data = request.get_json()
    user_id = data['user_id']

    user = Student.get_by_id(user_id)
    if not user:
        return f'User {user_id} not found', 404

    if user.calendar_id is None:
        logging.error(f'skipping: no calendar_id for user {user.student.email()}')
        return

    credentials = get_user_credentials_from_ae_datastore(user)
    if credentials is None:
        logging.error(f'skipping: no credentials for user {user.student.email()}')
        return

    calendar_service = build_calendar_service(user, credentials)
    try:
        calendar_exists = check_calendar_exists(calendar_service, user.calendar_id)
    except RefreshError as e:
        # credentials.refresh_token is None
        # URL being requested: GET https://www.googleapis.com/calendar/v3/users/me/calendarList/{calendarId}?alt=json
        # Refreshing credentials due to a 401 response. Attempt 1/2.
        # Exception on /import [GET]
        # google.auth.exceptions.RefreshError: The credentials do not contain the necessary fields need to refresh the access token. You must specify refresh_token, token_uri, client_id, and client_secret.
        #   https://google-auth.readthedocs.io/en/stable/reference/google.oauth2.credentials.html#google.oauth2.credentials.Credentials.refresh
        # Credentials object expired?
        #   https://google-auth.readthedocs.io/en/stable/reference/google.oauth2.credentials.html#google.oauth2.credentials.Credentials.expired
        #   https://google-auth.readthedocs.io/en/stable/reference/google.oauth2.credentials.html#google.oauth2.credentials.Credentials.valid
        logging.error(f'import was unsuccessful: credentials could not be refreshed for user {user.student.email()}')
        return
    else:
        if not calendar_exists:
            logging.error(f'skipping: non-existing calendar_id for user {user.student.email()}')
            return

    try:
        event_list = fetch_and_parse_week(user)
    except Exception as e:
        logging.error(e)
    else:
        if event_list:
            create_calendar_events(user, calendar_service, event_list)
            params={'user': user.student, 'calendar': user.calendar, 'events': event_list}
            mailer.send(recipient=user.student.email(),
                        message=render_template('email/notification.html', **params))
