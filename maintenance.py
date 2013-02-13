import logging
import webapp2
from models import Student, PermanentLinks


def _increment_or_delete(item):

    if (item.course == 5 and item.form == 10) or (item.course == 6 and item.form == 11):
        logging.debug("deleting: %s" % item)
        item.delete()
    else:
        logging.debug("incrementing: %s" % item)
        item.course += 1
        item.put()


def increment_course_and_cleanup_graduates():
    for student in Student.all().run():
        _increment_or_delete(student)

    for link in PermanentLinks.all().run():
        _increment_or_delete(link)


class MaintenanceTask(webapp2.RequestHandler):
    def get(self):
        increment_course_and_cleanup_graduates()


app = webapp2.WSGIApplication([('/maintenance', MaintenanceTask)], debug=True)

