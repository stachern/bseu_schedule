""" Constants used in this project """

# In the GAE console, the Cloud Datastore Viewer does not list models for which there are no entities.
# As such, gae_env initialises itself by adding a dummy setting.
# The name of this setting is INIT_KEY and it's value will be NOT_SET_VALUE.
# This way, users can easily find the GaeEnvSetting model in the Datastore viewer.
INIT_KEY = '___INIT_KEY___'

# The value set for a name, when it is not found.
# This way, when a name's value is NOT_SET_VALUE, it is still considered as not found.
# Initialising 'not found' settings to this value allows users to easily find the setting in the
#   Cloud Datastore viewer in the console and update it
NOT_SET_VALUE = '___NOT_SET___'

# Google App Engine supports namespaces.
# See https://cloud.google.com/appengine/docs/standard/python/multitenancy/ for more info
DEFAULT_GAE_NAMESPACE = ''
