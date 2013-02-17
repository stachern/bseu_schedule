from google.appengine.ext import db


class Event(object):

    def __init__(self, *args, **kwargs):
        for k, v in kwargs.iteritems():
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
    exists = PermanentLinks.all().filter("group =", group).filter("faculty =", faculty).filter("form =", form).filter("course = ", course).get()
    if exists:
        return exists.id
    else:
        link = PermanentLinks(group=group, faculty=faculty, form=form, course=course)
        link.put()
        return link.id


def save_event(event_list, creator):
    for event in event_list:
        new_schedule = Event(title=event['subject'],
                             description=event['description'],
                             location=event['location'],
                             starttime=event['date']['start'],
                             endtime=event['date']['end'],
                             creator=creator)
        new_schedule.put()


def create_or_update_student(user, request):
    existent = Student.all().filter("student =", user).get()
    if existent:
        if request.get('group'):
            existent.group = int(request.get('group'))
        if request.get('form'):
            existent.form = int(request.get('form'))
        if request.get('faculty'):
            existent.faculty = int(request.get('faculty'))
        if request.get('course'):
            existent.course = int(request.get('course'))
        current_calendar_name = request.get('calendar_name', False)
        current_calendar_id = request.get('calendar', False)
        if current_calendar_name and current_calendar_id:
            existent.calendar_id = current_calendar_id
            existent.calendar = current_calendar_name
            existent.auto = bool(request.get('auto', False))
        existent.put()
    else:
        Student(group=int(request.get('group')),
                form=int(request.get('form')),
                auto=bool(request.get('mode')),
                faculty=int(request.get('faculty')),
                course=int(request.get('course')),
                student=user,
                calendar_id=request.get('calendar'),
                calendar=request.get('calendar_name')).put()