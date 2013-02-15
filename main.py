#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# advanced bseu.by schedule parser
#

import os
import datetime
import urllib
import Cookie
import logging

from google.appengine.ext.webapp import template
from google.appengine.api import urlfetch, users
from handler import RequestHandler

from gaesessions import get_current_session
from models import Student, Event, add_permalink_and_get_key
import settings
from utils import schedule_parser, mailer, bseu_schedule

def _get_common_context():
    context = {'faculty_list': settings.BSEU_FACULTY_LIST}

    return context


class ScheduleApi(RequestHandler):
    def get_schedule_week(self, message, action):
        result = urlfetch.fetch(url=settings.BSEU_SCHEDULE_URL,
                                payload=urllib.urlencode(message),
                                method=urlfetch.POST,
                                headers=settings.HEADERS)
        if result.status_code == 200:
            if action == 'view':
                self.response.out.write(template.render(os.path.join(os.path.dirname(__file__),
                                                                     'templates/schedule.html'),
                                                        {'schedule': schedule_parser.show(result.content),
                                                         'uri': self.request.url}))
            elif action == 'save':
                try:
                    parsed_list = schedule_parser.read(result.content)
                except Exception, e:
                    logging.debug(e)
                    return "error: %s" % e
                else:
                    for parsed in parsed_list:
                        new_schedule = Event(title=parsed['subject'],
                                             description=parsed['description'],
                                             location=parsed['location'],
                                             starttime=parsed['date']['start'],
                                             endtime=parsed['date']['end'],
                                             creator=users.get_current_user())
                        if new_schedule.creator:
                            new_schedule.put()
                    self.redirect('/importer')

    def get(self):
        data = {}
        for field in self.request.arguments():
            if field == 'action':
                self.action = self.request.get(field)
            else:
                data[field] = self.request.get(field)

        data['__act'] = self.request.get('__act', settings.ACTION_ID)
        data['period'] = self.request.get('period', settings.BSEU_WEEK_PERIOD)
        self.get_schedule_week(data, self.action)


class MainPage(RequestHandler):
    """
    UI. let user authenticate log in params and sets task. also shows results
    """

    def get(self):
        self.response.headers['Content-Type'] = 'text/html'
        self.response.out.write(template.render("templates/html/main.html", self.get_context()))

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

        self.send_comment(self.request.get('comment'))
        user_profile.put()

    def get_context(self):
        self.user = users.get_current_user()
        self.session = get_current_session()
        context = _get_common_context()
        context['user'] = self.user
        if self.user:
            context['logout_url'] = users.create_logout_url('/')
        else:
            context['login_url'] = users.create_login_url('/')
        student = Student.all().filter("student =", users.get_current_user()).order("-lastrun").get()

        if student:
            context['permalink'] = add_permalink_and_get_key(student.group,
                                                             student.faculty,
                                                             student.course,
                                                             student.form)
            if student.calendar and not self.session.has_key('calendars'):
                context['calendar'] = {'saved': {'name': student.calendar}}
                if self.session.has_key('import'):
                    context['calendar']['imported'] = True
                    del self.session['import']
                context['auto_import'] = student.auto
            # replace to apply table styles
            context['schedule'] = {'week': bseu_schedule.fetch_and_show_week(student),
                                   'semester': bseu_schedule.fetch_and_show_semester(student)}

        if self.session.has_key('calendars'):
            context['calendar'] = {'picker': self.session['calendars']}
            del self.session['calendars']


        return context

    def send_comment(self, comm):
        logging.debug("comment from user: %s" % comm)
        if not comm is None and not comm == '':
            self.user = users.get_current_user()
            mailer.send(sender=self.user.email(),
                        recipient=settings.COMMENT_NOTIFICATION_RECIPIENT,
                        subject=settings.COMMENT_NOTIFICATION_SUBJECT,
                        message=comm)


class proxy(RequestHandler):
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
        self.response.out.write(template.render(os.path.join(os.path.dirname(__file__), 'templates/help.html'), {}))
