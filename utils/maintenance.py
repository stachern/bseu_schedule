import logging
from handler import RequestHandler
from models import Student, PermanentLinks
from gaesessions import delete_expired_sessions


def _increment_or_delete(item):

    if (item.course >= 5 and item.form == 10) or (item.course >= 6 and item.form == 11) or item.form < 10:
        logging.debug("deleting: %s" % item.id)
        item.delete()
    else:
        logging.debug("incrementing: %s" % item.id)
        item.course += 1
        item.put()


def increment_course_and_cleanup_graduates():
    for student in Student.all().run():
        _increment_or_delete(student)

    for link in PermanentLinks.all().run():
        _increment_or_delete(link)


class MaintenanceTask(RequestHandler):
    def get(self):
        increment_course_and_cleanup_graduates()
        while not delete_expired_sessions():
            pass



