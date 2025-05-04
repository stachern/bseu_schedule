from flask import Blueprint, render_template_string, request

import json
import logging
from gaesessions import delete_expired_sessions
from google.cloud import tasks_v2

from models import Student, PermanentLinks

from utils.decorators import admin_required, cron_only
from settings import APP_URL
from events_calendar import create_calendar_events_for_users_with_auto_import

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

# TODO: Come up with a better name, e.g.:
# * create_events_for_users()
# * create_events_weekly()
# * auto_import_weekly_events()
# * weekly_auto_import()?
# * auto_import_calendar_events_weekly()?
@task_handlers.route('/task/create_events')
@cron_only
def create_events():
    logging.info('starting batch insert job')
    create_calendar_events_for_users_with_auto_import()
    return render_template_string('success')


@task_handlers.post('/test-task-handler')
def test_task_handler():
    data = request.get_json()
    user_id = data['user_id']

    user = Student.get_by_id(user_id)
    if not user:
        return f'User {user_id} not found', 404

    logging.info(f'Processing user {user_id}: {user.student.email()}')

    return f'Processed user {user_id}', 200


@task_handlers.route('/task/test')
@admin_required
def test_task():
    client = tasks_v2.CloudTasksClient()

    project_id = 'bseu-api'
    location = 'us-central1'
    queue = 'test-queue'
    parent = client.queue_path(project_id, location, queue)

    url = f'{APP_URL}/test-task-handler'

    users = Student.all().filter("auto =", True).order("-lastrun").fetch(limit=1000)
    for user in users:
        user_id = user.key().id()
        task = {
            'http_request': {
                'http_method': tasks_v2.HttpMethod.POST,
                'url': url,
                'headers': {'Content-type': 'application/json'},
                'body': json.dumps({'user_id': user_id}).encode() # e.g. ID: 5629499534213120
            }
        }
        response = client.create_task(parent=parent, task=task)
        logging.info(f'Created task {response.name} for user {user_id}')

    return 'Tasks enqueued', 200
