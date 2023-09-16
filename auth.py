import logging

from google.appengine.api import users

from flask import Blueprint, render_template_string, redirect, request

from gaesessions import get_current_session
from settings import API_APP
import gdata.gauth
import gdata.calendar.data
import gdata.calendar.client

from utils.decorators import login_required

auth_handlers = Blueprint('auth_handlers', __name__)

logging.getLogger().setLevel(logging.DEBUG)
gcal = gdata.calendar.client.CalendarClient(source=API_APP['APP_NAME'])


# FIXME: Not working in production
@auth_handlers.route('/auth')
@login_required
def auth():
    """This handler is responsible for fetching an initial OAuth
    request token and redirecting the user to the approval page."""

    current_user = users.get_current_user()

    scopes = API_APP['SCOPES']
    oauth_callback = 'https://%s/calendar_auth' % request.host
    consumer_key = API_APP['CONSUMER_KEY']
    consumer_secret = API_APP['CONSUMER_SECRET']
    request_token = gcal.get_oauth_token(scopes, oauth_callback,
                                            consumer_key, consumer_secret)

    request_token_key = 'request_token_%s' % current_user.user_id()
    gdata.gauth.ae_save(request_token, request_token_key)

    approval_page_url = request_token.generate_authorization_url()
    return render_template_string(
        '<html><script type="text/javascript">window.location = "%s"</script></html>' % approval_page_url)


# FIXME: Not working in production
@auth_handlers.route('/calendar_auth')
@login_required
def oauth_callback():
    """When the user grants access, they are redirected back to this
    handler where their authorized request token is exchanged for a
    long-lived access token."""

    current_user = users.get_current_user()

    self.session = get_current_session()

    if self.session.is_active():
        self.session.terminate()

    request_token_key = 'request_token_%s' % current_user.user_id()
    request_token = gdata.gauth.ae_load(request_token_key)
    gdata.gauth.authorize_request_token(request_token, self.request.uri)
    gcal.auth_token = gcal.get_access_token(request_token)
    access_token_key = 'access_token_%s' % current_user.user_id()
    gdata.gauth.ae_save(request_token, access_token_key)

    try:
        feed = gcal.GetOwnCalendarsFeed()
        self.session['calendars'] = [{'title': a_calendar.title.text,
                                        'id': a_calendar.GetAlternateLink().href} for a_calendar in feed.entry]
    except UnicodeEncodeError as e:
        logging.error('error retrieving calendar list: %s' % e)

    else:
        return redirect('/edit')
