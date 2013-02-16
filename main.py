#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# advanced bseu.by schedule parser
#

import datetime
import urllib
import Cookie
import logging

from google.appengine.api import urlfetch, users
from handler import RequestHandler

from gaesessions import get_current_session
from models import Student, add_permalink_and_get_key, PermanentLinks
import settings
from utils import mailer, bseu_schedule


def _get_common_context():
    user = users.get_current_user()
    context = {'app_url': settings.APP_URL,
               'faculty_list': settings.BSEU_FACULTY_LIST,
               'user': user}
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
                                                         student.course,
                                                         student.form)
        if student.calendar and not session.has_key('calendars'):
            context['calendar'] = {'saved': {'name': student.calendar}}
            if session.has_key('import'):
                context['calendar']['imported'] = True
                del session['import']
            context['auto_import'] = student.auto
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
        context['link_key'] = add_permalink_and_get_key(form=int(self.request.get('form')),
                                                        course=int(self.request.get('course')),
                                                        group=int(self.request.get('group')),
                                                        faculty=int(self.request.get('faculty')))
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
        existent = Student.all().filter("student =", users.get_current_user()).get()
        if not existent is None:
            if self.request.get('group'):
                existent.group = int(self.request.get('group'))
            if self.request.get('form'):
                existent.form = int(self.request.get('form'))
            existent.auto = bool(int(self.request.get('mode')))
            if self.request.get('faculty'):
                existent.faculty = int(self.request.get('faculty'))
            if self.request.get('course'):
                existent.course = int(self.request.get('course'))
            existent.lastrun = datetime.datetime.now()
            current_calendar_name = self.request.get('calendar_name', False)
            current_calendar_id = self.request.get('calendar', False)
            if current_calendar_name and current_calendar_id:
                existent.calendar_id = current_calendar_id
                existent.calendar = current_calendar_name
            user_profile = existent
        else:
            user_profile = Student(group=int(self.request.get('group')),
                                   form=int(self.request.get('form')),
                                   auto=bool(self.request.get('mode')),
                                   faculty=int(self.request.get('faculty')),
                                   course=int(self.request.get('course')),
                                   student=users.get_current_user(),
                                   lastrun=datetime.datetime.now(),
                                   calendar_id=self.request.get('calendar'),
                                   calendar=self.request.get('calendar_name'))
        user_profile.put()

        self.get()


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
        self.render_to_response('templates/html/help.html', {})
