""" Class definitions for Cloud Datastore entities"""

from google.appengine.ext import ndb

__all__ = ['GaeEnvSettings']


class GaeEnvSettings(ndb.Model):  # pylint: disable=R0903
    """ Environment variables/settings stored in Cloud Datastore
    as name-value pairs.

    Names are unique and values are stored as string
    """
    name = ndb.StringProperty(required=True, indexed=True)
    value = ndb.StringProperty(required=True, indexed=False)
