#!/usr/bin/env python
# -*- coding: utf-8 -*-
# advanced bseu.by schedule parcer
#

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
from gaesessions import get_current_session
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util, template
from google.appengine.api import urlfetch, users
from models import Student, Event
import datetime
import urllib, Cookie
import logging
import scheduleparser, settings, mailer


logging.getLogger().setLevel(logging.DEBUG)


class apihandler(webapp.RequestHandler):
    def get_schedule_week(self, message, action):
        data = urllib.urlencode(message)
        url = settings.BSEUURL
        result = urlfetch.fetch(url=url,
            payload=data,
            method=urlfetch.POST,
            headers=settings.HEADERS)
        if result.status_code == 200:
            if action == 'view':
                self.response.out.write(template.render(os.path.join(os.path.dirname(__file__), 'templates/schedule.html'), {'schedule':scheduleparser.show(result.content), 'uri':self.request.url}))
            elif action == 'save':
                try:
                    parsedlist = scheduleparser.read(result.content)
                except Exception, e:
                    logging.debug(e)
                    return "unseccess: %s" % e
                else:
                    for parsed in parsedlist:
                        new_sched = Event(title=parsed['subject'],
                            description=parsed['description'],
                            location=parsed['location'],
                            starttime=parsed['date']['start'],
                            endtime=parsed['date']['end'],
                            creator=users.get_current_user())
                        if new_sched.creator:
                            new_sched.put()
                    self.redirect('/importer')
    def get(self):
        data = {}
        for field in self.request.arguments():
            if field == 'action':
                self.action = self.request.get(field)
            else:
                data[field] = self.request.get(field)
        data['__act'] = self.request.get('__act', '__id.25.main.inpFldsA.GetSchedule__sp.7.results__fp.4.main')
        data['period'] = self.request.get('period', 2)
        self.data = data
        self.get_schedule_week(self.data, self.action)


class main_page(webapp.RequestHandler):
    """
    UI. let user authenticate log in params and sets task. also shows results
    """

    def get(self, *args, **kwargs):
        self.user = users.get_current_user()
        self.session=get_current_session()
        self.response.headers['Content-Type'] = 'text/html'
        self.context={}
        if self.user:
            self.context['account']={'username':self.user.nickname(),'logout_url':users.create_logout_url("/")}
        else:
            self.context['account']={'login_url':users.create_login_url("/")}
        self.check_settings()
        self.response.out.write(template.render(os.path.join(os.path.dirname(__file__), 'templates/main.html'), self.context))

    def post(self):
        existent = Student.all().filter("student =", users.get_current_user()).get()
        if not existent is None:
            existent.group = int(self.request.get('group'))
            existent.form = int(self.request.get('form'))
            existent.auto = bool(self.request.get('mode'))
            existent.faculty = int(self.request.get('faculty'))
            existent.course = int(self.request.get('course'))
            existent.lastrun = datetime.datetime.now()
            curcalname = self.request.get('calendar_name', False)
            curcalid = self.request.get('calendar', False)
            if curcalname and curcalid:
                existent.calendar_id = curcalid
                existent.calendar = curcalname
            userprofile = existent
        else:
            userprofile = Student(group=int(self.request.get('group')),
                form=int(self.request.get('form')),
                auto=bool(self.request.get('mode')),
                faculty=int(self.request.get('faculty')),
                course=int(self.request.get('course')),
                student=users.get_current_user(),
                lastrun=datetime.datetime.now(),
                calendar_id=self.request.get('calendar'),
                calendar=self.request.get('calendar_name'))

        self.send_comment(self.request.get('comment'))
        userprofile.put()

    def check_settings(self):

        user_settings = Student.all().filter("student =", users.get_current_user()).order("-lastrun").get()

        if not user_settings is None:
            self.context['permalink'] = settings.ARGS % (
            user_settings.faculty, user_settings.group, user_settings.course, user_settings.form)
            if user_settings.calendar and not self.session.has_key('calendars'):
                self.context['calendar']={'saved':{'name':user_settings.calendar}}
                if self.session.has_key('import'):
                    self.context['calendar']['imported']=True
                    del self.session['import']

        if self.session.has_key('calendars'):
            self.context['calendar'] = {'picker':self.session['calendars']}
            del self.session['calendars']

    def send_comment(self, comm):
        logging.debug("comment from user: %s" % comm)
        if not comm is None and not comm == '':
            self.user = users.get_current_user()
            mailer.send(sender=self.user.email(),
                            recipient=settings.to,
                            subject=settings.subject,
                            message=comm)


class proxy(webapp.RequestHandler):
    def _fake(self):
        self.head = settings.HEADERS
        self.cookie = Cookie.SimpleCookie()
        result = urlfetch.fetch(url=settings.BSEUURL, method=urlfetch.GET,
            headers=self.head)
        self.cookie.load(result.headers.get('set-cookie', ''))

    def get(self):
        self._fake()
        dat = {}
        for field in self.request.arguments():
            dat[field] = self.request.get(field)
        result = urlfetch.fetch(url=settings.BSEUURL, payload=urllib.urlencode(dat), method=urlfetch.POST,
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


class help_page(webapp.RequestHandler):
    def get(self):
        self.response.out.write(template.render(os.path.join(os.path.dirname(__file__), 'templates/help.html'),{}))


def main():
    application = webapp.WSGIApplication([('/scheduleapi', apihandler),
        ('/', main_page),
        ('/help', help_page),
        ('/proxy', proxy)],
        debug=False)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
