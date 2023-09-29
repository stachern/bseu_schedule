import gae_env

class ClientConfig(object):
    _instance = None

    @classmethod
    def instance(self):
        if not self._instance:
            self._instance = {'client_id': gae_env.get('client_id', raise_value_not_set_error=False),
                            'client_secret': gae_env.get('client_secret', raise_value_not_set_error=False) }
        return self._instance
