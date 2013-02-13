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

    @property
    def id(self):
        return str(self.key())

    def __repr__(self):
        return self.student.name


class PermanentLinks(db.Model):

    group = db.IntegerProperty()
    faculty = db.IntegerProperty()
    form = db.IntegerProperty()
    course = db.IntegerProperty()

    @property
    def id(self):
        return str(self.key())

    def __repr__(self):
        return "Link: course=%s, form=%s" % (self.course, self.form)


def add_permalink_and_get_key(group, faculty, form, course):
    exists = PermanentLinks.all().filter("group =", group).filter("faculty =", faculty).filter("form =", form).filter("course = ", course).get()
    if exists:
        return exists.id
    else:
        link = PermanentLinks(group=group, faculty=faculty, form=form, course=course)
        link.put()
        return link.id