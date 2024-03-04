import logging

from google.appengine.api import mail
from flask import render_template


def send(recipient, message=False, params=False, subject='BSEU schedule import',
         sender='import@bseu-api.appspotmail.com'):
    logging.info("sending email: from %s; to %s; subject: %s; body: %s" % (sender, recipient, subject, message))
    if params:
        mail.send_mail(sender=sender, to=recipient, subject=subject,
                       body=render_template('email/notification.html', **params))
    if message:
        mail.send_mail(sender=sender, to=recipient, subject=subject, body=message)
