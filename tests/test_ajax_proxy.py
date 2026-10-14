import json
from unittest import TestCase, mock

from google.appengine.ext import testbed


class GAETestCase(TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.setup_env(app_id='bseu-api', GAE_VERSION='test')

    def tearDown(self):
        self.testbed.deactivate()


class TestAjaxProxy(GAETestCase):

    def _client(self):
        from main import app
        app.config['TESTING'] = True
        return app.test_client()

    @mock.patch('main.bseu_schedule.is_bseu_marked_down', return_value=False)
    @mock.patch('main.requests.post')
    def test_proxy_returns_bseu_down_on_405(self, post, _is_down):
        response = mock.Mock()
        response.ok = False
        response.status_code = 405
        post.return_value = response

        rv = self._client().get('/proxy?faculty=14')

        self.assertEqual(rv.status_code, 200)
        self.assertEqual(json.loads(rv.data), {'error': 'bseu_down'})

    @mock.patch('main.bseu_schedule.mark_bseu_down')
    @mock.patch('main.bseu_schedule.is_bseu_marked_down', return_value=False)
    @mock.patch('main.requests.post')
    def test_proxy_marks_bseu_down_on_503(self, post, _is_down, mark_down):
        response = mock.Mock()
        response.ok = False
        response.status_code = 503
        post.return_value = response

        rv = self._client().get('/proxy?faculty=14')

        self.assertEqual(rv.status_code, 200)
        self.assertEqual(json.loads(rv.data), {'error': 'bseu_down'})
        mark_down.assert_called_once_with()
