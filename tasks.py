from flask import Blueprint, render_template, render_template_string

import logging
from gaesessions import delete_expired_sessions

from models import Student, PermanentLinks

from utils import mailer, bseu_schedule
from utils.decorators import admin_required, cron_only
from events_calendar import build_calendar_service, check_calendar_exists, create_calendar_events

from auth import get_user_credentials_from_ae_datastore

from google.auth.exceptions import RefreshError

task_handlers = Blueprint('task_handlers', __name__)

def _is_stale_fulltime(item):
    return item.form == 10 and \
         ((item.faculty != 263 and item.course > 4) or (item.faculty == 263 and item.course > 5))

def _is_stale_parttime(item):
    return item.form == 11 and \
         ((item.faculty != 129 and item.course > 5) or (item.faculty == 127 and item.course > 3))

def _is_stale(item):
    return _is_stale_fulltime(item) or \
           _is_stale_parttime(item) or \
           (item.form == 61 and item.course > 4)

def _increment_or_delete(item):
    if _is_stale(item):
        logging.debug("deleting: %s" % item.id)
        item.delete()
    else:
        logging.debug("incrementing: %s" % item.id)
        item.course += 1
        item.put()

def increment_course_and_cleanup_graduates():
    for student in Student.all().run():
        _increment_or_delete(student)

    for link in PermanentLinks.all().run():
        _increment_or_delete(link)

def _cleanup_sessions():
    while not delete_expired_sessions():
        pass

@task_handlers.route('/task/maintenance')
@admin_required
def maintenance():
    increment_course_and_cleanup_graduates()
    _cleanup_sessions()
    return render_template_string('success')

@task_handlers.route('/task/create_events')
@cron_only
def create_events():
    logging.info('starting batch insert job')
    users = Student.all().filter("auto =", True).order("-lastrun").fetch(limit=1000)
    for user in users:
        credentials = get_user_credentials_from_ae_datastore(user)
        if user.calendar_id is None or credentials is None:
            logging.error(f'skipping: no calendar_id or credentials for user {user.student.email()}')
            continue

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
            continue
        else:
            if not calendar_exists:
                logging.error(f'skipping: non-existing calendar_id for user {user.student.email()}')
                continue

        try:
            event_list = bseu_schedule.fetch_and_parse_week(user)
        except Exception as e:
            logging.error(e)
        else:
            if event_list:
                create_calendar_events(user, calendar_service, event_list)
                params={'user': user.student, 'calendar': user.calendar, 'events': event_list}
                mailer.send(recipient=user.student.email(),
                            message=render_template('email/notification.html', **params))
    return render_template_string('success')
