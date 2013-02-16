from handler import RequestHandler
from models import PermanentLinks
import settings


class ResolveLink(RequestHandler):
    def get(self, key):
        student = PermanentLinks.get(key)
        self.redirect('%sscheduleapi?%s' % (settings.APP_URL, settings.SCHEDULE_VIEW_ARGS % (
            student.faculty, student.group, student.course, student.form
        )))


