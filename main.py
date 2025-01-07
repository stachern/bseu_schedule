#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# advanced bseu.by schedule parser
#
import os

from urllib.parse import urlencode
import logging

from google.appengine.api import users, wrap_wsgi_app
import requests

from flask import Flask, render_template, render_template_string, request, redirect

from gaesessions import get_current_session
from models import Student, PermanentLinks
from models import add_permalink_and_get_key, create_or_update_student
import settings
from markupsafe import escape
from utils import mailer, bseu_schedule
from utils.helpers import _flash

# Import handlers defined in the corresponding Blueprints
from auth import auth_handlers
from events_calendar import import_handlers
from tasks import task_handlers

from gaesessions import SessionMiddleware

COOKIE_KEY = 'oib23b234,mnasd[f898yhk4jblafiuhd2jk341m2n3vb'

app = Flask(__name__)
app.wsgi_app = SessionMiddleware(app.wsgi_app, cookie_key=COOKIE_KEY)
# TODO: Include recording.appstats_wsgi_middleware if possible.
app.wsgi_app = wrap_wsgi_app(app.wsgi_app)

# Register blueprints, so that any route matching what's defined there
# will get routed to them
app.register_blueprint(auth_handlers)
app.register_blueprint(import_handlers)
app.register_blueprint(task_handlers)

def _get_app_version():
    return os.environ['GAE_VERSION']


def _get_common_context():
    session = get_current_session()
    user = users.get_current_user()
    context = {'app_url': settings.APP_URL,
               'faculty_list': settings.BSEU_FACULTY_LIST,
               'user': user,
               'app_version': _get_app_version()}
    if 'messages' in session:
        context['messages'] = session['messages']
        del session['messages']
    if user:
        context['logout_url'] = users.create_logout_url('/')
    else:
        context['login_url'] = users.create_login_url('/')
    return context


def get_anonymous_context():
    context = _get_common_context()
    return context


def get_user_context():
    session = get_current_session()
    context = _get_common_context()

    student = Student.all().filter("student =", users.get_current_user()).order("-lastrun").get()

    if student:
        context['student'] = student
        context['link_key'] = add_permalink_and_get_key(student.group,
                                                        student.faculty,
                                                        student.form,
                                                        student.course)
        # replace to apply table styles
        context['schedule'] = {'week': bseu_schedule.fetch_and_show_week(student),
                           'semester': bseu_schedule.fetch_and_show_semester(student)}

    if 'calendars' in session:
        context['calendar'] = {'picker': session['calendars']}
        del session['calendars']

    return context


def send_comment(comment_text):
    logging.debug("comment from user: %s" % comment_text)
    if not comment_text is None and not comment_text == '':
        user = users.get_current_user()
        mailer.send(sender=user.email(),
                    recipient=settings.COMMENT_NOTIFICATION_RECIPIENT,
                    subject=settings.COMMENT_NOTIFICATION_SUBJECT,
                    message=comment_text)


@app.route('/schedule')
@app.route('/scheduleapi') # legacy
def schedule():
    context = get_anonymous_context()
    try:
        args = request.args
        context['link_key'] = add_permalink_and_get_key(form=args.get('form', type=int),
                                                        course=args.get('course', type=int),
                                                        group=args.get('group', type=int),
                                                        faculty=args.get('faculty', type=int))
    except ValueError:
        return redirect('/')
    else:
        links = PermanentLinks.get(context['link_key'])
        context['schedule'] = {'week': bseu_schedule.fetch_and_show_week(links),
                                'semester': bseu_schedule.fetch_and_show_semester(links)}
        return render_template('html/main.html', **context)


@app.get('/')
def root():
    return render_template("html/main.html", **get_user_context())

@app.post('/')
def find_or_update_current_user_schedule():
    user = users.get_current_user()
    if user:
        # Update current user's schedule on form submit
        create_or_update_student(user, request)
        # return render_template("html/main.html", **get_user_context())
        return redirect('/')

    # Find a schedule
    try:
        #user is anonymous
        form = request.form
        key = add_permalink_and_get_key(form=form.get('form', type=int),
                                        course=form.get('course', type=int),
                                        group=form.get('group', type=int),
                                        faculty=form.get('faculty', type=int))
        return redirect('/link/' + key)
    except ValueError:
        return redirect('/')


@app.route('/edit')
def edit_page():
    context = get_user_context()
    context['action'] = 'edit'
    return render_template("html/main.html", **context)


@app.route('/proxy')
def ajax_proxy():
    dat = {}
    args = request.args
    for field in args:
        dat[field] = args.get(field)
    try:
        result = requests.post(settings.BSEU_SCHEDULE_URL,
                               data=urlencode(dat),
                               headers=settings.HEADERS)
        result.raise_for_status()
        return render_template_string(result.content.decode("utf-8"))
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
        # This handles the 500 error when bseu.by is down!
        url = settings.BSEU_SCHEDULE_URL
        logging.exception(f"[ajax_proxy] {url} is currently unresponsive: {e}")
        _flash(u"Сайт расписания БГЭУ перегружен или недоступен, попробуйте позже.")
        return {"error": "bseu_down"}

@app.route('/help')
def help():
    return render_template('html/help.html', **get_user_context())

@app.post('/comment')
def comment():
    send_comment(request.form['comment'])
    _flash(u"Комментарий успешно отправлен!")
    return ""

@app.route('/link/<key>')
def resolve_link(key):
    """This is basically to keep old links valid"""
    student = PermanentLinks.get(escape(key))
    return redirect('/schedule?%s' % (settings.SCHEDULE_VIEW_ARGS % (
        student.faculty, student.group, student.course, student.form
    )))

@app.route('/privacy')
def privacy():
    return render_template('html/privacy.html', **get_user_context())

@app.route('/disclosure')
def disclosure():
    return render_template('html/disclosure.html', **get_user_context())
