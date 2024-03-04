# coding: utf-8

import os
import logging

from client_config import ClientConfig

from google.appengine.api import users

from flask import Blueprint, redirect, request, url_for

from gaesessions import get_current_session

import requests
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

from oauthlib.oauth2.rfc6749.errors import MissingCodeError

from utils.decorators import login_required
from utils.helpers import _flash
from utils.ae_helpers import ae_save, ae_load

from settings import OAUTH2_CONFIG, OAUTH2_SCOPES


auth_handlers = Blueprint('auth_handlers', __name__)

logging.getLogger().setLevel(logging.DEBUG)


@auth_handlers.route('/auth')
@login_required
def authorize():
    """This route is responsible for fetching an initial OAuth 2.0
    state and redirecting the user to the OAuth consent screen."""

    # Use ClientConfig to identify the application requesting authorization.
    # The client ID (from that file) and access scopes are required.
    flow = Flow.from_client_config(ClientConfig.instance(), scopes=OAUTH2_SCOPES)

    # Indicate where the API server will redirect the user after the user completes
    # the authorization flow. The redirect URI is required. The value must exactly
    # match one of the authorized redirect URIs for the OAuth 2.0 client, which was
    # configured in the API Console for the Google OAuth consent screen. If this value
    # doesn't match an authorized URI, you will get a 'redirect_uri_mismatch' error.
    flow.redirect_uri = url_for('auth_handlers.oauth2_callback', _external=True)

    # Generate URL for request to Google's OAuth 2.0 server.
    authorization_url, state = flow.authorization_url(
        # Enable offline access so that you can refresh an access token without
        # re-prompting the user for permission. Recommended for web server apps.
        access_type='offline',
        # Enable incremental authorization. Recommended as a best practice.
        include_granted_scopes='true')

    # Store the state so the callback can verify the auth server response.
    session = get_current_session()
    session['state'] = state

    return redirect(authorization_url)


def credentials_to_dict(credentials, refresh_token):
    return {'token': credentials.token,
            'refresh_token': (credentials.refresh_token or refresh_token),
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes}

@auth_handlers.route('/calendar_auth')
@login_required
def oauth2_callback():
    """When the user grants access, they are redirected to this route where
    their authorization code is exchanged for a long-lived access token."""

    # When running locally, disable OAuthlib's HTTPs verification.
    # This is to get rid of the following error in development:
    #   InsecureTransportError: (insecure_transport) OAuth 2 MUST utilize https.
    if os.environ.get('GAE_ENV') == 'localdev':
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

    session = get_current_session()
    current_user = users.get_current_user()

    # Specify the state when creating the flow in the callback so that it can be
    # verified in the authorization server response.
    state = session['state']
    flow = Flow.from_client_config(ClientConfig.instance(), scopes=OAUTH2_SCOPES, state=state)
    flow.redirect_uri = url_for('auth_handlers.oauth2_callback', _external=True)

    try:
        # Use authorization server's response to fetch OAuth 2.0 token.
        flow.fetch_token(authorization_response=request.url)
    except MissingCodeError as e:
        # When a user clicks Cancel instead of Continue (giving their consent):
        #   MissingCodeError: (missing_code) Missing code parameter in response.
        #   http://localhost:8080/calendar_auth?error=access_denied&state=some_refresh_token
        _flash(u'Не удалось авторизовать приложение.', session)
        return redirect('/')

    credentials = flow.credentials
    # Subsequent calls to oauth2_callback return 'None' as 'refresh_token'
    # from 'flow.credentials', so make sure to replace it with the existing
    # value from credentials in the session before setting.
    session['credentials'] = credentials_to_dict(
        credentials, session.get('credentials', {}).get('refresh_token'))

    # Store user's access and refresh tokens in the App Engine datastore.
    refresh_token = credentials.refresh_token
    if refresh_token is not None:
        refresh_token_key = 'refresh_token_%s' % current_user.user_id()
        ae_save(refresh_token, refresh_token_key)

    access_token = credentials.token
    access_token_key = 'access_token_%s' % current_user.user_id()
    ae_save(access_token, access_token_key)

    try:
        calendar_service = build('calendar', 'v3', credentials=credentials, cache_discovery=False)

        # CalendarList#list API ref:
        #   https://developers.google.com/calendar/api/v3/reference/calendarList/list
        calendar_list = calendar_service.calendarList().list().execute()
        session['calendars'] = [{'title': calendar['summary'],
                                    'id': calendar['id']} for calendar in calendar_list['items']]
    except UnicodeEncodeError as e:
        logging.error('error retrieving calendar list: %s' % e)

    else:
        return redirect('/edit')


# https://developers.google.com/identity/protocols/oauth2/web-server#example
@auth_handlers.route('/clear')
def clear_credentials():
    session = get_current_session()

    if 'credentials' in session:
        del session['credentials']
        del session['state']
        _flash('User credentials have been cleared.', session)

    return redirect('/')


# https://developers.google.com/identity/protocols/oauth2/web-server#example
@auth_handlers.route('/revoke')
def revoke_credentials():
    """This route revokes permissions that the user has already granted to the application."""

    session = get_current_session()

    if 'credentials' not in session:
        _flash('You need to authorize the app before trying to revoke credentials!', session)
        return redirect('/')

    access_token = session['credentials']['token']

    # https://developers.google.com/identity/protocols/oauth2/web-server#tokenrevoke
    revoke = requests.post('https://oauth2.googleapis.com/revoke',
        allow_redirects=False,
        params={'token': access_token},
        headers={'content-type': 'application/x-www-form-urlencoded'})

    status_code = getattr(revoke, 'status_code')
    if status_code == 200:
        _flash('Credentials successfully revoked!', session)
    else:
        _flash('An error occurred!', session)

    return redirect('/')


def get_user_credentials_from_session(user):
    session = get_current_session()

    if not 'credentials' in session:
        return redirect('/auth')

    # Store user's access and refresh tokens in the App Engine datastore.
    # FYI: TEMPORARY SOLUTION!
    # TODO: Remove once all users' refresh and access tokens are in the datastore!
    user_id = user.student.user_id()
    refresh_token = session['credentials'].get('refresh_token')
    if refresh_token is not None:
        refresh_token_key = 'refresh_token_%s' % user_id
        ae_save(refresh_token, refresh_token_key)
    access_token = session['credentials'].get('token')
    if access_token is not None:
        access_token_key = 'access_token_%s' % user_id
        ae_save(access_token, access_token_key)

    # https://developers.google.com/identity/protocols/oauth2/web-server#example
    # Load user credentials from the session stored in App Engine datastore
    return Credentials(**session['credentials'])

def get_user_credentials_from_ae_datastore(user):
    user_id = user.student.user_id()
    access_token_key = 'access_token_%s' % user_id
    access_token = ae_load(access_token_key)
    if access_token is None:
        logging.info('[get_user_credentials_from_ae_datastore] no access token for user %s - skipping' % user_id)
        return

    refresh_token_key = 'refresh_token_%s' % user_id
    refresh_token = ae_load(refresh_token_key)
    if refresh_token is None:
        logging.info('[get_user_credentials_from_ae_datastore] no refresh token for user %s - skipping' % user_id)
        return

    # https://developers.google.com/identity/protocols/oauth2/web-server#example
    config = ClientConfig.instance()['web']
    return Credentials(
        token=access_token,
        refresh_token=refresh_token,
        token_uri=OAUTH2_CONFIG['token_uri'],
        scopes=OAUTH2_SCOPES,
        client_id=config['client_id'],
        client_secret=config['client_secret'])
