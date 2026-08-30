import os
import settings

from google.cloud import secretmanager

# Cache secrets to avoid repeated API calls
_secret_cache = {}

def get_secret(secret_id, version_id='latest'):
    cache_key = f"{secret_id}:{version_id}"
    if cache_key in _secret_cache:
        return _secret_cache[cache_key]

    client = secretmanager.SecretManagerServiceClient()

    name = f"projects/{settings.PROJECT_ID}/secrets/{secret_id}/versions/{version_id}"

    response = client.access_secret_version(name=name)
    secret_value = response.payload.data.decode('utf-8')

    _secret_cache[cache_key] = secret_value

    return secret_value

def get_secret_or_env(secret_id, default=None):
    """Use Secret Manager in production, env variables locally."""

    # Use env variables in development
    if os.environ.get('GAE_ENV') == 'localdev':
        return os.environ.get(secret_id, default)

    # Use Secret Manager in producction
    return get_secret(secret_id)
