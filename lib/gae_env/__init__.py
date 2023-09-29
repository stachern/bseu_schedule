"""
Easily accessible environment variables on Google App Engine, stored in Cloud Datastore.

"""
# pylint: disable=C0413, C0411

import os

from .utils import run_in_namespace
from .models import GaeEnvSettings
from .constants import INIT_KEY, NOT_SET_VALUE, DEFAULT_GAE_NAMESPACE
from .errors import ValueNotSetError


__all__ = ['get', 'set_value', 'ValueNotSetError']


def get(
        name, raise_value_not_set_error=True, gae_namespace=DEFAULT_GAE_NAMESPACE,
        converter_class=str, return_none_for_not_set_value=True
):
    # region docstring
    """ Get the value stored at a key.
    Key/name is first looked up in the system environment variables and if not found,
    Cloud Datastore.

    By looking up the system environment variables first, we ensure that variables defined in
    project's app.yaml are not overshadowed

    Args:
        name {str} -- The name of the variable

    Keyword Arguments:
        raise_not_found_error {bool} -- If True,
            then a ValueNotSetError is raised if the key has no value set.
            (default: {True})
        gae_namespace {str} -- If the key is stored in Cloud Datastore,
            fetch it from this namespace (default: {''})
        converter_class {type} -- The type to convert the value to, before returning.
            Supported types include, str, int, float
        return_none_for_not_set_value {bool} -- If True, returns None if the value of a key/name is NOT_SET_VALUE

    Returns:
        {str|int|float|None} -- The value stored for the key/name.
            The type of the value depends on :converter_class:
            However, if :return_none_for_not_set_value: is True, None will be returned for :name:s with no set value

    Raises:
        ValueNotSetError -- If kwarg :raise_value_not_set_error: is True and no value has been set for :name:/key
        ValueError -- If the stored value is not of type :converter_class:
    """
    # endregion

    if converter_class not in (str, int, float):
        raise ValueError("'%s' is invalid for arg converter_class" % str(converter_class))

    value = __get_value_from_system_env(name) or \
        run_in_namespace(__get_value_from_datastore, gae_namespace, name=name)

    if value is None:
        set_value(name, NOT_SET_VALUE)  # initialise it to a dummy value in Cloud Datastore
        value = NOT_SET_VALUE

    if raise_value_not_set_error and (value == NOT_SET_VALUE):
        raise ValueNotSetError(key=name)
    elif return_none_for_not_set_value and (value == NOT_SET_VALUE):
        return None  # return None, if no value had been set
    else:
        return converter_class(value)


def set_value(name, value, gae_namespace=DEFAULT_GAE_NAMESPACE):
    # type: (str, str) -> None
    """ Set a value for a name/key.
    For any value, it's string representation is what is stored

    NB: This sets the value in Cloud Datastore only!
    """
    run_in_namespace(__set_value_for_name_in_datastore, gae_namespace, name=name, value=value)


def __get_value_from_datastore(name):
    # type: (str) -> str
    """ Get the value for a name from Cloud Datastore
    """
    setting = GaeEnvSettings.query(
        GaeEnvSettings.name == str(name)).get()  # type: GaeEnvSettings
    if not setting:
        return None
    return setting.value  # type: str


def __get_value_from_system_env(name):
    """Get the value for a name from system environment variables"""
    return os.environ.get(name)


def __set_value_for_name_in_datastore(name, value):
    """ Set value for a name/key in Cloud Datastore
    """
    setting = GaeEnvSettings.query(
        GaeEnvSettings.name == str(name)).get()  # type: GaeEnvSettings
    if setting is None:
        setting = GaeEnvSettings(name=str(name))
    setting.value = str(value)
    setting.put()



def init():
# Initialize the underlying datastore Model, GaeEnvSettings

# The Datastore Viewer does not list models for which no entity has been registered.
# By initialising, we create a dummy entity, so that the model becomes visible
# in the Datastore Viewer.
# This way, users can easily add values for names in the Developers Console.
    try:
        get(INIT_KEY)
    except ValueNotSetError:
        pass
