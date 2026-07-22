from flask import Blueprint, render_template_string, request

import json
import logging
from gaesessions import delete_expired_sessions
from google.cloud import tasks_v2

from models import Student, PermanentLinks

from utils.decorators import admin_required, cron_only

from settings import APP_URL, AUTO_IMPORT_QUEUE, LOCATION, PROJECT_ID

AUTO_IMPORT_HANDLER_URL = f'{APP_URL}/auto-import'

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

@task_handlers.route('/task/enqueue-auto-import-tasks')
@cron_only
def enqueue_auto_import_tasks():
    """This cron job enqueues a separate Cloud Tasks task on the AUTO_IMPORT_QUEUE queue
    for each student with auto import enabled, and each task is then handled by the
    `/auto-import` route."""

    logging.info('Starting enqueueing auto import tasks')

    cloud_tasks_client = tasks_v2.CloudTasksClient()
    parent = cloud_tasks_client.queue_path(PROJECT_ID, LOCATION, AUTO_IMPORT_QUEUE)

    users = Student.all().filter("auto =", True).order("-lastrun").fetch(limit=1000)
    for user in users:
        user_id = user.key().id()
        task = {
            'http_request': {
                'http_method': tasks_v2.HttpMethod.POST,
                'url': AUTO_IMPORT_HANDLER_URL,
                'headers': {'Content-type': 'application/json'},
                'body': json.dumps({'user_id': user_id}).encode() # e.g. ID: 5629499534213120
            }
        }
        response = cloud_tasks_client.create_task(parent=parent, task=task)
        logging.info(f'Created task {response.name} for user {user_id}')

    return 'Tasks enqueued', 200
