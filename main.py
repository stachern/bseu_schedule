#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# advanced bseu.by schedule parser
#
import os

import urllib
import Cookie
import logging
import datetime

from google.appengine.api import urlfetch, users
from handler import RequestHandler

from gaesessions import get_current_session
from models import Student, PermanentLinks
from models import add_permalink_and_get_key, create_or_update_student
import settings
from utils import mailer, bseu_schedule


def _get_app_version():
    # get app version
    app_version, timestamp = os.environ['CURRENT_VERSION_ID'].split('.')
    app_version_time = datetime.datetime.fromtimestamp(long(timestamp) / pow(2, 28)).strftime("%d/%m/%y")
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

    if session.has_key('calendars'):
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


class ScheduleApi(RequestHandler):
    def get(self):
        context = get_anonymous_context()
        try:
            context['link_key'] = add_permalink_and_get_key(form=int(self.request.get('form')),
                                                            course=int(self.request.get('course')),
                                                            group=int(self.request.get('group')),
                                                            faculty=int(self.request.get('faculty')))
        except ValueError:
            self.redirect('/')
        else:
            links = PermanentLinks.get(context['link_key'])
            context['schedule'] = {'week': bseu_schedule.fetch_and_show_week(links),
                                   'semester': bseu_schedule.fetch_and_show_semester(links)}
            self.render_to_response('templates/html/main.html', context)


class MainPage(RequestHandler):
    """
    UI. let user authenticate log in params and sets task. also shows results
    """

    def get(self):
        self.render_to_response("templates/html/main.html", get_user_context())

    def post(self):
        """This handles pretty much all the changes"""
        user = users.get_current_user()
        if user:
            create_or_update_student(user, self.request)
            self.get()
        else:
            try:
                #user is anonymous
                key = add_permalink_and_get_key(form=int(self.request.get('form')),
                                                course=int(self.request.get('course')),
                                                group=int(self.request.get('group')),
                                                faculty=int(self.request.get('faculty')))
                self.redirect('link/' + key)
            except ValueError:
                self.redirect('/')


class EditPage(RequestHandler):
    def get(self):
        context = get_user_context()
        context['action'] = 'edit'
        self.render_to_response("templates/html/main.html", context)


class AjaxProxy(RequestHandler):
    def _fake(self):
        self.head = settings.HEADERS
        self.cookie = Cookie.SimpleCookie()
        result = urlfetch.fetch(url=settings.BSEU_SCHEDULE_URL, method=urlfetch.GET,
                                headers=self.head)
        self.cookie.load(result.headers.get('set-cookie', ''))

    def get(self):
        self._fake()
        dat = {}
        for field in self.request.arguments():
            dat[field] = self.request.get(field)
        result = urlfetch.fetch(url=settings.BSEU_SCHEDULE_URL, payload=urllib.urlencode(dat), method=urlfetch.POST,
                                headers=self._getHeaders(self.cookie))
        self.response.out.write(result.content)

    def _makeCookieHeader(self, cookie):
        cookieHeader = ""
        for value in cookie.values():
            cookieHeader += "%s=%s; " % (value.key, value.value)
        return cookieHeader

    def _getHeaders(self, cookie):
        self.head['Cookie'] = self._makeCookieHeader(cookie)
        return self.head


class HelpPage(RequestHandler):
    def get(self):
        self.render_to_response('templates/html/help.html', get_user_context())


class CommentHandler(RequestHandler):
    def post(self):
        send_comment(self.request.get('comment'))
        self.response.out.write('Comment is sent!')
