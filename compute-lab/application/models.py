__author__ = 'peersp'

from google.appengine.ext import ndb

class Lab(ndb.Model):
    """Data model to record labs"""
    name = ndb.StringProperty()
    project_id = ndb.StringProperty()
    lab_zone = ndb.StringProperty()

class Instance(ndb.Model):
    """Data model to record instances"""
    name = ndb.StringProperty()
    lab = ndb.KeyProperty(kind=Lab)
    desired_state = ndb.StringProperty()
    request_timestamp = ndb.DateTimeProperty()