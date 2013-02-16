from handler import RequestHandler
from models import PermanentLinks
import settings


class ResolveLink(RequestHandler):
    """This is basically to keep old links valid"""
    def get(self, key):
        student = PermanentLinks.get(key)
        self.redirect('/schedule?%s' % (settings.SCHEDULE_VIEW_ARGS % (
            student.faculty, student.group, student.course, student.form
        )))


