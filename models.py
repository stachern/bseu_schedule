from google.appengine.ext import db

class Event(object):

    def __init__(self, *args, **kwargs):
        for k, v in kwargs.items():
            super(Event, self).__setattr__(k, v)


class Student(db.Model):
    group = db.IntegerProperty()
    faculty = db.IntegerProperty()
    form = db.IntegerProperty()
    course = db.IntegerProperty()
    auto = db.BooleanProperty()
    lastrun = db.DateTimeProperty(auto_now=True)
    student = db.UserProperty(required=True)
    calendar = db.TextProperty()
    calendar_id = db.TextProperty()

    @property
    def id(self):
        return str(self.key())

    def __repr__(self):
        return self.student.nickname


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
    exists = PermanentLinks.all().filter("group =", group)\
        .filter("faculty =", faculty).filter("form =", form).filter("course = ", course).get()
    if exists:
        return exists.id
    else:
        link = PermanentLinks(group=group, faculty=faculty, form=form, course=course)
        link.put()
        return link.id


def _create_student(user, form):
    return Student(group=form.get('group', type=int),
                   form=form.get('form', type=int),
                   auto=form.get('auto', type=bool),
                   faculty=form.get('faculty', type=int),
                   course=form.get('course', type=int),
                   student=user,
                   calendar_id=form.get('calendar'),
                   calendar=form.get('calendar_name')).put()


def create_or_update_student(user, request):
    student = Student.all().filter("student =", user).get()
    form = request.form
    if not student:
        return _create_student(user, form)

    if form.get('group'):
        student.group = form.get('group', type=int)
    if form.get('form'):
        student.form = form.get('form', type=int)
    if form.get('faculty'):
        student.faculty = form.get('faculty', type=int)
    if form.get('course'):
        student.course = form.get('course', type=int)
    current_calendar_name = form.get('calendar_name', default=False)
    current_calendar_id = form.get('calendar', default=False)
    if current_calendar_name and current_calendar_id:
        student.calendar_id = current_calendar_id
        student.calendar = current_calendar_name
        student.auto = form.get('auto', default=False, type=bool)
    student.put()
