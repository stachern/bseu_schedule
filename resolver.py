import webapp2
from models import PermanentLinks
import settings


class ResolveLink(webapp.RequestHandler):
    def get(self, period, key):
        student = PermanentLinks.get(key)
        self.redirect('%sscheduleapi?period=%s&%s' % (settings.APP_URL, period, settings.SCHEDULE_VIEW_ARGS % (
            student.faculty, student.group, student.course, student.form
        )))



app = webapp2.WSGIApplication([('/link/(\d)/?(.*)', ResolveLink)], debug=False)

