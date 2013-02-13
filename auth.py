import logging

from google.appengine.ext.webapp.util import login_required
from google.appengine.api import users
import webapp2

from gaesessions import get_current_session
from settings import API_APP
import gdata.gauth
import gdata.calendar.data
import gdata.calendar.client


logging.getLogger().setLevel(logging.DEBUG)
gcal = gdata.calendar.client.CalendarClient(source=API_APP['APP_NAME'])


class Auth(webapp2.RequestHandler):
    @login_required
    def get(self):
        """This handler is responsible for fetching an initial OAuth
        request token and redirecting the user to the approval page."""

        current_user = users.get_current_user()

        scopes = API_APP['SCOPES']
        oauth_callback = 'http://%s/calendar_auth' % self.request.host
        consumer_key = API_APP['CONSUMER_KEY']
        consumer_secret = API_APP['CONSUMER_SECRET']
        request_token = gcal.get_oauth_token(scopes, oauth_callback,
            consumer_key, consumer_secret)

        request_token_key = 'request_token_%s' % current_user.user_id()
        gdata.gauth.ae_save(request_token, request_token_key)

        approval_page_url = request_token.generate_authorization_url()
        self.response.out.write(
            '<html><script type="text/javascript">window.location = "%s"</script></html>' % approval_page_url)


class RequestTokenCallback(webapp2.RequestHandler):

    @login_required
    def get(self):
        """When the user grants access, they are redirected back to this
        handler where their authorized request token is exchanged for a
        long-lived access token."""

        current_user = users.get_current_user()

        self.session=get_current_session()

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
            self.session['calendars'] = [{'title':a_calendar.title.text, 'id':a_calendar.GetAlternateLink().href} for a_calendar in feed.entry]
        except UnicodeEncodeError, e:
            logging.error('error retrieving calendar list: %s' % e)

        else:
            self.redirect('/')


app = webapp2.WSGIApplication([('/auth', Auth),
                              ('/calendar_auth', RequestTokenCallback)],
                              debug=True)
