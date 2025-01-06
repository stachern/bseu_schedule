from flask import Blueprint, render_template_string

import logging
from gaesessions import delete_expired_sessions

from models import Student, PermanentLinks

from utils import mailer, bseu_schedule
from utils.decorators import admin_required, cron_only
from events_calendar import create_calendar_events

from auth import get_user_credentials_from_ae_datastore

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
        if user.calendar_id and credentials:
            try:
                event_list = bseu_schedule.fetch_and_parse_week(user)
            except Exception as e:
                logging.error(e)
            else:
                if event_list:
                    create_calendar_events(user, credentials, event_list)
                    mailer.send(recipient=user.student.email(),
                                params={'user': user.student, 'calendar': user.calendar, 'events': event_list})
    return render_template_string('success')
