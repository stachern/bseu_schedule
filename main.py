#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# advanced bseu.by schedule parser
#
import os

from six.moves import urllib, http_cookies
import logging
import datetime

from google.appengine.api import urlfetch, users

from flask import Flask, render_template, render_template_string, request, redirect

from gaesessions import get_current_session
from models import Student, PermanentLinks
from models import add_permalink_and_get_key, create_or_update_student
import settings
from markupsafe import escape
from utils import mailer, bseu_schedule

# Import handlers defined in the corresponding Blueprints
from auth import auth_handlers
from events_calendar import import_handlers
from tasks import task_handlers

app = Flask(__name__)

# Register blueprints, so that any route matching what's defined there
# will get routed to them
app.register_blueprint(auth_handlers)
app.register_blueprint(import_handlers)
app.register_blueprint(task_handlers)

def _get_app_version():
    # get app version
    app_version, timestamp = os.environ['CURRENT_VERSION_ID'].split('.')
    app_version_time = datetime.datetime.fromtimestamp(int(timestamp) // pow(2, 28)).strftime("%d/%m/%y")
    app_version += ' from %s' % app_version_time
    return app_version


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


@app.route('/', methods=['GET', 'POST'])
def root():
    if request.method == 'GET':
        return render_template("html/main.html", **get_user_context())

    else:
        """This handles pretty much all the changes"""
        user = users.get_current_user()
        if user:
            create_or_update_student(user, request)
            # return render_template("html/main.html", **get_user_context())
            return redirect('/')  # update user's schedule on form submit
        else:
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


# ajax_proxy related
def _fake():
    request.headers = settings.HEADERS
    request.cookie = http_cookies.SimpleCookie()
    result = urlfetch.fetch(url=settings.BSEU_SCHEDULE_URL,
                            method=urlfetch.GET,
                            headers=request.headers)
    request.cookie.load(result.headers.get('set-cookie', ''))

def _makeCookieHeader(cookie):
    cookieHeader = ""
    for value in list(cookie.values()):
        cookieHeader += "%s=%s; " % (value.key, value.value)
    return cookieHeader

def _getHeaders(cookie):
    request.headers['Cookie'] = _makeCookieHeader(cookie)
    return request.headers

@app.route('/proxy')
def ajax_proxy():
    _fake()
    dat = {}
    args = request.args
    for field in args:
        dat[field] = args.get(field)
    result = urlfetch.fetch(url=settings.BSEU_SCHEDULE_URL,
                            payload=urllib.parse.urlencode(dat),
                            method=urlfetch.POST,
                            headers=_getHeaders(request.cookie))
    return render_template_string(result.content.decode("utf8"))

@app.route('/help')
def help():
    return render_template('html/help.html', **get_user_context())

@app.route('/comment', methods=['POST'])
def comment():
    send_comment(request.form['comment'])
    # TODO: show flash instead, as the text below is useless and not seen by the user!
    return render_template_string('Comment is sent!')

@app.route('/link/<key>')
def resolve_link(key):
    """This is basically to keep old links valid"""
    student = PermanentLinks.get(escape(key))
    return redirect('/schedule?%s' % (settings.SCHEDULE_VIEW_ARGS % (
        student.faculty, student.group, student.course, student.form
    )))
