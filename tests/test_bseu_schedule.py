from unittest import TestCase, mock

import requests

from google.appengine.ext import testbed

import settings
from utils import bseu_schedule


class GAETestCase(TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.setup_env(app_id='bseu-api')


class TestBseuDownFlag(GAETestCase):

    @mock.patch('utils.bseu_schedule.memcache')
    def test_is_bseu_marked_down_when_flag_missing(self, memcache):
        memcache.get.return_value = None
        self.assertFalse(bseu_schedule.is_bseu_marked_down())

    @mock.patch('utils.bseu_schedule.memcache')
    def test_is_bseu_marked_down_when_flag_set(self, memcache):
        memcache.get.return_value = True
        self.assertTrue(bseu_schedule.is_bseu_marked_down())

    @mock.patch('utils.bseu_schedule.memcache')
    def test_mark_bseu_down_sets_memcache_key(self, memcache):
        bseu_schedule.mark_bseu_down()
        memcache.set.assert_called_once_with(
            settings.BSEU_DOWN_KEY, True, time=settings.BSEU_DOWN_TTL_SECONDS)

    @mock.patch('utils.bseu_schedule.requests.post')
    @mock.patch('utils.bseu_schedule.is_bseu_marked_down', return_value=True)
    def test_fetch_raises_without_calling_bseu_when_marked_down(self, _is_down, post):
        with self.assertRaises(bseu_schedule.BseuUnavailableError):
            bseu_schedule._fetch_raw_html_schedule.__wrapped__(1, 2, 3, 4)

        post.assert_not_called()

    @mock.patch('utils.bseu_schedule.mark_bseu_down')
    @mock.patch('utils.bseu_schedule.is_bseu_marked_down', return_value=False)
    @mock.patch('utils.bseu_schedule.requests.post', side_effect=requests.exceptions.ConnectTimeout())
    def test_fetch_marks_bseu_down_on_connect_timeout(self, post, _is_down, mark_down):
        with self.assertRaises(requests.exceptions.ConnectTimeout):
            bseu_schedule._fetch_raw_html_schedule.__wrapped__(1, 2, 3, 4)

        mark_down.assert_called_once_with()
