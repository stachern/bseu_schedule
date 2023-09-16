from flask import Blueprint, render_template_string

import logging
from gaesessions import delete_expired_sessions

from models import Student, PermanentLinks

from utils import mailer, bseu_schedule
from utils.decorators import admin_required
from events_calendar import create_calendar_events

task_handlers = Blueprint('task_handlers', __name__)

def _increment_or_delete(item):
    if (item.course >= 5 and item.form == 10) or (item.course >= 6 and item.form == 11) or item.form < 10:
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

@task_handlers.route('/task/maintenance')
@admin_required
def maintenance():
    increment_course_and_cleanup_graduates()
    while not delete_expired_sessions():
        pass
    return render_template_string('success')

@task_handlers.route('/task/create_events')
@admin_required
def create_events():
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
    return render_template_string('success')
