import logging
import os

from google.appengine.api import mail
from google.appengine.ext.webapp import template  # TODO: Change!
import settings


def send(recipient, message=False, params=False, subject='BSEU schedule import',
         sender='import@bseu-api.appspotmail.com'):
    logging.info("sending email: from %s; to %s; subject: %s; body: %s" % (sender, recipient, subject, message))
    if params:
        mail.send_mail(sender=sender, to=recipient, subject=subject,
                       body=template.render(os.path.join(settings.ROOT_PATH, 'templates/email/notification.html'),
                                            params))
    if message:
        mail.send_mail(sender=sender, to=recipient, subject=subject, body=message)
