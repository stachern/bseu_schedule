import logging

from google.appengine.api import mail


def send(recipient, message=False, subject='BSEU schedule import', sender='import@bseu-api.appspotmail.com'):
    if not message:
        return

    logging.info("sending email: from %s; to %s; subject: %s; body: %s" % (sender, recipient, subject, message))
    mail.send_mail(sender=sender, to=recipient, subject=subject, body=message)
