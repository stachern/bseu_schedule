import os
from unittest import TestCase, mock

from google.appengine.ext import testbed

import auth
from events_calendar import handle_expired_credentials, handle_missing_calendar


class GAETestCase(TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.setup_env(app_id='bseu-api')


class TestStoredRefreshToken(GAETestCase):

    @mock.patch('auth.ae_load')
    def test_user_has_stored_refresh_token_when_present(self, ae_load):
        ae_load.return_value = 'stored-token'
        self.assertTrue(auth.user_has_stored_refresh_token('user-123'))
        ae_load.assert_called_once_with('refresh_token_user-123')

    @mock.patch('auth.ae_load')
    def test_user_has_stored_refresh_token_when_missing(self, ae_load):
        ae_load.return_value = None
        self.assertFalse(auth.user_has_stored_refresh_token('user-123'))


class TestDeleteUserTokens(GAETestCase):

    @mock.patch('auth.ae_delete')
    def test_deletes_access_and_refresh_tokens(self, ae_delete):
        auth.delete_user_tokens('user-123')
        ae_delete.assert_any_call('access_token_user-123')
        ae_delete.assert_any_call('refresh_token_user-123')
        self.assertEqual(ae_delete.call_count, 2)


class TestHandleExpiredCredentials(GAETestCase):

    def setUp(self):
        super().setUp()
        self.user = mock.Mock()
        self.user.auto = True
        self.user.student.user_id.return_value = 'user-123'
        self.user.student.email.return_value = 'student@example.com'

    @mock.patch('events_calendar.render_template', return_value='email body')
    @mock.patch('events_calendar.mailer.send')
    @mock.patch('events_calendar.delete_user_tokens')
    def test_disables_auto_import_and_notifies_user(self, delete_user_tokens, mailer_send, render_template):
        handle_expired_credentials(self.user, source='auto-import')

        self.assertFalse(self.user.auto)
        self.user.put.assert_called_once_with()
        delete_user_tokens.assert_called_once_with('user-123')
        render_template.assert_called_once_with(
            'email/credentials_expired.html',
            user=self.user.student)
        mailer_send.assert_called_once_with(
            recipient='student@example.com',
            subject='BSEU Schedule: reconnect Google Calendar',
            message='email body')

    @mock.patch('events_calendar.render_template', return_value='email body')
    @mock.patch('events_calendar.mailer.send')
    @mock.patch('events_calendar.delete_user_tokens')
    def test_skips_put_when_auto_import_already_disabled(self, delete_user_tokens, mailer_send, render_template):
        self.user.auto = False

        handle_expired_credentials(self.user, source='auto-import')

        self.user.put.assert_not_called()
        delete_user_tokens.assert_called_once_with('user-123')
        mailer_send.assert_called_once()

    @mock.patch('events_calendar.render_template', return_value='email body')
    @mock.patch('events_calendar.mailer.send')
    @mock.patch('events_calendar.delete_user_tokens')
    def test_accepts_custom_reason(self, delete_user_tokens, mailer_send, render_template):
        with self.assertLogs('root', level='WARNING') as logs:
            handle_expired_credentials(
                self.user,
                source='auto-import',
                reason='no credentials in datastore')

        self.assertTrue(any('no credentials in datastore' in message for message in logs.output))
        delete_user_tokens.assert_called_once_with('user-123')
        mailer_send.assert_called_once()

    @mock.patch('events_calendar.mailer.send')
    @mock.patch('events_calendar.render_template', return_value='email body')
    @mock.patch('auth.ae_delete')
    @mock.patch('auth.ae_load')
    def test_recovery_loop_clears_stored_refresh_token(self, ae_load, ae_delete, render_template, mailer_send):
        ae_load.return_value = 'stale-token'

        self.assertTrue(auth.user_has_stored_refresh_token('user-123'))

        handle_expired_credentials(self.user, source='auto-import')

        ae_delete.assert_any_call('access_token_user-123')
        ae_delete.assert_any_call('refresh_token_user-123')

        ae_load.return_value = None
        self.assertFalse(auth.user_has_stored_refresh_token('user-123'))


class TestHandleMissingCalendar(GAETestCase):

    def setUp(self):
        super().setUp()
        self.user = mock.Mock()
        self.user.auto = True
        self.user.calendar_id = 'cal-123'
        self.user.calendar = 'My Calendar'
        self.user.student.user_id.return_value = 'user-123'
        self.user.student.email.return_value = 'student@example.com'

    @mock.patch('events_calendar.render_template', return_value='email body')
    @mock.patch('events_calendar.mailer.send')
    def test_disables_auto_import_clears_calendar_and_notifies_user(self, mailer_send, render_template):
        handle_missing_calendar(self.user, source='auto-import')

        self.assertFalse(self.user.auto)
        self.assertIsNone(self.user.calendar_id)
        self.assertIsNone(self.user.calendar)
        self.user.put.assert_called_once_with()
        render_template.assert_called_once_with(
            'email/calendar_not_found.html',
            user=self.user.student,
            calendar='My Calendar')
        mailer_send.assert_called_once_with(
            recipient='student@example.com',
            subject='BSEU Schedule: Google Calendar not found',
            message='email body')

    @mock.patch('events_calendar.render_template', return_value='email body')
    @mock.patch('events_calendar.mailer.send')
    def test_does_not_delete_oauth_tokens(self, mailer_send, render_template):
        with mock.patch('events_calendar.delete_user_tokens') as delete_user_tokens:
            handle_missing_calendar(self.user, source='auto-import')

        delete_user_tokens.assert_not_called()
        mailer_send.assert_called_once()
