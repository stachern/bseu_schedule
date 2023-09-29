""" Custom exceptions for this lib """

from .constants import NOT_SET_VALUE

class ValueNotSetError(Exception):
    """ Error raised when no value has been set for a key/name.

    A key/name's value is considered not set if its corresponding entity is not found at all
    or its value is `constants.NOT_SET_VALUE`.

    For any key/name whose corresponding entity is not found at all,
    it is initialised with a value of `constants.NOT_SET_VALUE` in Cloud Datastore
    """
    def __init__(self, key):
        message = 'No value has been set for the key/name: %s.' % key
        message += (
            "A dummy value: '%s' has been created for this key/name " +
            'Go to the Datastore Viewer in the console for your project' +
            'on App Engine, look up the GaeEnvSetting entity with name=%s ' +
            'and update its value'
        ) % (NOT_SET_VALUE, key)
        super(ValueNotSetError, self).__init__(message)
