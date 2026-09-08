#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import timedelta
import logging
import time

from google.appengine.ext import db
from google.appengine.api import users

from utils import mailer
from utils.decorators import login_required
from utils.bseu_schedule import fetch_and_parse_week, BseuUnavailableError
from utils.helpers import _flash

from auth import (
    get_user_credentials_from_session,
    get_user_credentials_from_ae_datastore,
    persist_refreshed_access_token,
    delete_user_tokens,
)

from flask import Blueprint, render_template, redirect, request

from models import Student

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.exceptions import RefreshError

DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S.000Z'
MAX_INSERT_RETRIES = 3
INSERT_RETRY_SECONDS = 1

CREDENTIALS_EXPIRED_SUBJECT = 'BSEU Schedule: reconnect Google Calendar'
CALENDAR_NOT_FOUND_SUBJECT = 'BSEU Schedule: Google Calendar not found'

import_handlers = Blueprint('import_handlers', __name__)


def handle_expired_credentials(user, source='auto-import', reason='credentials could not be refreshed'):
    """Disable auto-import and notify the user when OAuth credentials are unusable."""
    user_id = user.student.user_id()
    logging.warning(f"[{source}] {reason} for user {user_id}; disabling auto-import")

    if user.auto:
        user.auto = False
        user.put()

    delete_user_tokens(user_id)

    mailer.send(
        recipient=user.student.email(),
        subject=CREDENTIALS_EXPIRED_SUBJECT,
        message=render_template('email/credentials_expired.html', user=user.student))


def handle_missing_calendar(user, source='auto-import', reason='Google Calendar not found'):
    """Disable auto-import and notify the user when the selected calendar is gone."""
    user_id = user.student.user_id()
    calendar_name = user.calendar
    logging.warning(f"[{source}] {reason} for user {user_id}; disabling auto-import")

    user.auto = False
    user.calendar_id = None
    user.calendar = None
    user.put()

    mailer.send(
        recipient=user.student.email(),
        subject=CALENDAR_NOT_FOUND_SUBJECT,
        message=render_template(
            'email/calendar_not_found.html',
            user=user.student,
            calendar=calendar_name))


def _is_rate_limit_error(error):
    if not isinstance(error, HttpError):
        return False
    if error.resp.status == 429:
        return True
    if error.resp.status == 403:
        content = error.content.decode('utf-8') if error.content else str(error)
        return 'rateLimitExceeded' in content or 'userRateLimitExceeded' in content
    return False


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

    for attempt in range(MAX_INSERT_RETRIES + 1):
        try:
            # Events#insert API ref: https://developers.google.com/calendar/api/v3/reference/events/insert
            calendar_service.events().insert(calendarId=user_calendar, body=event).execute()
        except HttpError as e:
            if _is_rate_limit_error(e) and attempt < MAX_INSERT_RETRIES:
                time.sleep(INSERT_RETRY_SECONDS * (2 ** attempt))
                continue
            logging.warning(f"import was unsuccessful - skipping event: {e}")
            return False
        except Exception as e:
            logging.warning(f"import was unsuccessful - skipping event: {e}")
            return False
        else:
            logging.debug(f"import was successful: {event['summary']}-{event['description']}")
            return True

    return False


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
        if not insert_event(calendar_service, event, user.calendar_id):
            return False

    return True


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
        persist_refreshed_access_token(user, credentials)
    except RefreshError:
        handle_expired_credentials(user, source='manual-import')
        _flash(u'Не удалось импортировать расписание. Повторите попытку еще раз')
        return redirect('/auth')
    else:
        if not calendar_exists:
            logging.warning(f'import was unsuccessful: non-existing calendar_id for user {user.student.email()}')
            _flash(u'Не удалось импортировать расписание. Выбранный календарь не найден!')
            return redirect('/')

    try:
        event_list = fetch_and_parse_week(user)
    except BseuUnavailableError:
        _flash(u'Не удалось импортировать расписание. Сайт расписания БГЭУ перегружен или недоступен, попробуйте позже')
        return redirect('/')
    except IndexError:
        _flash(u'Не удалось импортировать расписание. Расписание не найдено')
    except Exception as e:
        logging.error(e)
    else:
        if create_calendar_events(user, calendar_service, event_list):
            _flash(u'Расписание успешно добавлено в календарь!')
        else:
            _flash(u'Не удалось импортировать расписание. Повторите попытку еще раз')

    return redirect('/')


@import_handlers.post('/auto-import')
def auto_import_calendar_events():
    data = request.get_json()
    user_id = data['user_id']

    user = Student.get_by_id(user_id)
    if not user:
        return f'User {user_id} not found', 404

    if user.calendar_id is None:
        handle_missing_calendar(user, source='auto-import', reason='no calendar_id configured')
        return f'calendar_id for user {user_id} not found', 404

    credentials = get_user_credentials_from_ae_datastore(user)
    if credentials is None:
        handle_expired_credentials(user, source='auto-import', reason='no credentials in datastore')
        return f'Credentials for user {user_id} not found', 403

    calendar_service = build_calendar_service(user, credentials)
    try:
        calendar_exists = check_calendar_exists(calendar_service, user.calendar_id)
        persist_refreshed_access_token(user, credentials)
    except RefreshError:
        handle_expired_credentials(user, source='auto-import')
        return f'Credentials for user {user_id} could not be refreshed', 403
    else:
        if not calendar_exists:
            calendar_id = user.calendar_id
            handle_missing_calendar(user, source='auto-import', reason='Google Calendar not found')
            return f'calendar_id {calendar_id} for user {user_id} does not exist', 404

    try:
        event_list = fetch_and_parse_week(user)
    except BseuUnavailableError:
        return f'bseu.by is currently unavailable', 503
    except IndexError:
        return f'Schedule not found for user {user_id}', 404
    except Exception as e:
        logging.error(e)
        return 'Unexpected error while fetching and parsing schedule', 500
    else:
        if event_list:
            if create_calendar_events(user, calendar_service, event_list):
                params={'user': user.student, 'calendar': user.calendar, 'events': event_list}
                mailer.send(recipient=user.student.email(),
                            message=render_template('email/notification.html', **params))
            else:
                return f'Calendar import failed for user {user_id}', 500

    return f'Auto import for user {user_id} completed successfully', 200
