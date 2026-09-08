from datetime import datetime
from unittest import TestCase, mock

import httplib2
from google.appengine.ext import testbed
from googleapiclient.errors import HttpError

from events_calendar import (
    _is_rate_limit_error,
    create_calendar_events,
    insert_event,
    MAX_INSERT_RETRIES,
)


class GAETestCase(TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.setup_env(app_id='bseu-api')


def _http_error(status, content):
    response = httplib2.Response({'status': str(status), 'content-type': 'application/json'})
    return HttpError(response, content.encode('utf-8'))


class TestRateLimitHandling(GAETestCase):

    def test_detects_rate_limit_on_403(self):
        error = _http_error(403, '{"error":{"errors":[{"reason":"rateLimitExceeded"}]}}')
        self.assertTrue(_is_rate_limit_error(error))

    def test_detects_rate_limit_on_429(self):
        error = _http_error(429, '{"error":{"message":"Too Many Requests"}}')
        self.assertTrue(_is_rate_limit_error(error))

    def test_ignores_other_http_errors(self):
        error = _http_error(404, '{"error":{"message":"Not Found"}}')
        self.assertFalse(_is_rate_limit_error(error))


class TestInsertEvent(GAETestCase):

    def _schedule_event(self):
        return mock.Mock(
            title='Subject',
            description='Lecture',
            location='1/101',
            starttime=datetime(2026, 9, 1, 10, 0),
            endtime=datetime(2026, 9, 1, 11, 0),
        )

    def _calendar_service(self, side_effect):
        calendar_service = mock.Mock()
        calendar_service.events.return_value.insert.return_value.execute.side_effect = side_effect
        return calendar_service

    @mock.patch('events_calendar.time.sleep')
    def test_retries_rate_limited_insert(self, sleep):
        rate_limit = _http_error(403, '{"error":{"errors":[{"reason":"rateLimitExceeded"}]}}')
        calendar_service = self._calendar_service([rate_limit, None])

        result = insert_event(calendar_service, self._schedule_event(), 'cal-123')

        self.assertTrue(result)
        self.assertEqual(
            calendar_service.events.return_value.insert.return_value.execute.call_count,
            2)
        sleep.assert_called_once()

    @mock.patch('events_calendar.time.sleep')
    def test_returns_false_after_exhausted_retries(self, sleep):
        rate_limit = _http_error(403, '{"error":{"errors":[{"reason":"rateLimitExceeded"}]}}')
        calendar_service = self._calendar_service([rate_limit] * (MAX_INSERT_RETRIES + 2))

        with self.assertLogs('root', level='WARNING'):
            result = insert_event(calendar_service, self._schedule_event(), 'cal-123')

        self.assertFalse(result)
        self.assertEqual(sleep.call_count, MAX_INSERT_RETRIES)

    @mock.patch('events_calendar.insert_event', side_effect=[True, False, True])
    @mock.patch('events_calendar.time.sleep')
    def test_create_calendar_events_stops_after_first_failure(self, sleep, insert_event_mock):
        user = mock.Mock(calendar_id='cal-123')
        calendar_service = mock.Mock()
        events = [mock.Mock(), mock.Mock(), mock.Mock()]

        result = create_calendar_events(user, calendar_service, events)

        self.assertFalse(result)
        self.assertEqual(insert_event_mock.call_count, 2)
        sleep.assert_not_called()

    @mock.patch('events_calendar.insert_event', return_value=True)
    def test_create_calendar_events_returns_true_when_all_succeed(self, insert_event_mock):
        user = mock.Mock(calendar_id='cal-123')
        calendar_service = mock.Mock()
        events = [mock.Mock(), mock.Mock()]

        result = create_calendar_events(user, calendar_service, events)

        self.assertTrue(result)
        self.assertEqual(insert_event_mock.call_count, 2)
