#!/usr/bin/env python
# -*- coding: utf-8 -*-

from gaesessions import get_current_session
from google.appengine.ext import webapp, db
from google.appengine.ext.webapp.util import run_wsgi_app, login_required
from google.appengine.api import urlfetch, users
from models import Student, Event
from settings import BSEUURL, HEADERS, API_APP
from datetime import timedelta, time
import gdata.gauth
import gdata.calendar.data
import gdata.calendar.client
import atom.data
import scheduleparser, mailer, urllib, logging


logging.getLogger().setLevel(logging.DEBUG)
gcal = gdata.calendar.client.CalendarClient(source=API_APP['APP_NAME'])

def InsertSingleEvent(calendar_client, title='bseu-api event',
                      content='study hard', where='in space',
                      start_time=None, end_time=None, ucalendar=None):
    event = gdata.calendar.data.CalendarEventEntry()
    event.title = atom.data.Title(text=title)
    event.content = atom.data.Content(text=content)
    event.where.append(gdata.calendar.data.CalendarWhere(value=where))

    if start_time is None:
        # Use current time for the start_time and have the event last 1 hour
        start_time = time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime())
        end_time = time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime(time.time() + 3600))
    else:
        start_time = (start_time - timedelta(hours=3)).strftime('%Y-%m-%dT%H:%M:%S.000Z')
        end_time = (end_time - timedelta(hours=3)).strftime('%Y-%m-%dT%H:%M:%S.000Z')

    event.when.append(gdata.calendar.data.When(start=start_time, end=end_time))

    try:
        if ucalendar is None:
            calendar_client.InsertEvent(event)
        else:
            calendar_client.InsertEvent(event, ucalendar)
    except Exception, e:
        logging.error('import was unsuccessfull - skipping: %s'  % e)
    else:
        logging.debug('import was successfull: %s-%s' % (title, content))


def eventimport(who):
    access_token_key = 'access_token_%s' % who.student.user_id()
    gcal.auth_token = gdata.gauth.ae_load(access_token_key)
    results = Event.all().filter("creator =", who.student).order("starttime").fetch(limit=30)
    batch = []
    for event in results:
        InsertSingleEvent(gcal, event.title, event.description, event.location, event.starttime, event.endtime,
            who.calendar_id)
        batch.append(event)
    db.delete(batch)


def fetch(who):
    data = {
    '__act' : '__id.25.main.inpFldsA.GetSchedule__sp.7.results__fp.4.main',
    'period' : 2,
    'faculty' : who.faculty,
    'group' : who.group,
    'course' : who.course,
    'form' : who.form
    }

    data = urllib.urlencode(data)
    result = urlfetch.fetch(url=BSEUURL,
        payload=data,
        method=urlfetch.POST,
        headers=HEADERS)
    try:
        parsedlist = scheduleparser.read(result.content)
    except Exception, e:
        logging.error(e)
    else:
        for parsed in parsedlist:
            new_sched = Event(title=parsed['subject'],
                description=parsed['description'],
                location=parsed['location'],
                starttime=parsed['date']['start'],
                endtime=parsed['date']['end'],
                creator=who.student)
            new_sched.put()




class Importer(webapp.RequestHandler):
    @login_required
    def get(self):
        user_settings = Student.all().filter("student =", users.get_current_user()).order("-lastrun").get()
        eventimport(user_settings)
        self.session=get_current_session()
        self.session['import']=True
        self.redirect('/')

class BatchFetcher(webapp.RequestHandler):
    def get(self):
        logging.info('starting batch fetch job')
        results = Student.all().filter("auto =", True).order("-lastrun").fetch(limit=1000)
        for stud in results:
            if stud.calendar:
                fetch(stud)
        self.response.out.write('success')


class BatchInserter(webapp.RequestHandler):
    def get(self):
        logging.info('starting batch insert job')
        results = Student.all().filter("auto =", True).order("-lastrun").fetch(limit=1000)
        for stud in results:
            if stud.calendar:
                eventimport(stud)
                mailer.send( recipient=stud.student.email(), params={'user':stud.student,'week': 15 })
        self.response.out.write('success')

def main():
    application = webapp.WSGIApplication([
        ('/importer', Importer),
        ('/batchfetcher', BatchFetcher),
        ('/batchinserter', BatchInserter)],
        debug=False)

    run_wsgi_app(application)

if __name__ == '__main__':
    main()

