from handler import RequestHandler
from models import PermanentLinks
import settings


class ResolveLink(RequestHandler):
    def get(self, period, key):
        student = PermanentLinks.get(key)
        self.redirect('%sscheduleapi?period=%s&%s' % (settings.APP_URL, period, settings.SCHEDULE_VIEW_ARGS % (
            student.faculty, student.group, student.course, student.form
        )))


