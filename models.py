from google.appengine.ext import ndb


class Account(ndb.Model):
    """Account entity - represents user account used to post article"""
    name = ndb.StringProperty(required=True)
    password = ndb.StringProperty(required=True)
    email = ndb.StringProperty(required=True)


class Article(ndb.Model):
    """Article entity - represents blog article"""
    title = ndb.StringProperty(required=True)
    body = ndb.StringProperty()
    date_time_created = ndb.DateTimeProperty(required=True)
    date_time_last_edited = ndb.DateTimeProperty(required=True)
    account_key = ndb.KeyProperty(required=True, kind=Account)
