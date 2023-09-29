import gae_env
from settings import OAUTH2_CONFIG

class ClientConfig(object):
    _instance = None

    @classmethod
    def instance(self):
        if not self._instance:
            config = {'client_id': gae_env.get('client_id'), 'client_secret': gae_env.get('client_secret')}
            config.update(OAUTH2_CONFIG)
            self._instance = { 'web': config }
        return self._instance
