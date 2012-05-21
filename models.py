from google.appengine.ext import db

class Event(db.Model):
    """
    temporary storage
    """
    title = db.StringProperty(required=True)
    description = db.TextProperty()
    starttime = db.DateTimeProperty()
    endtime = db.DateTimeProperty()
    location = db.TextProperty()
    creator = db.UserProperty()


class Student(db.Model):
    group = db.IntegerProperty()
    faculty = db.IntegerProperty()
    form = db.IntegerProperty()
    course = db.IntegerProperty()
    auto = db.BooleanProperty()
    lastrun = db.DateTimeProperty()
    student = db.UserProperty(required=True)
    calendar = db.TextProperty()
    calendar_id = db.TextProperty()