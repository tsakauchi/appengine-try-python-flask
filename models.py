from google.appengine.ext import ndb


class Account(ndb.Model):
    """Account entity - represents user account used to post article"""

    dispname = ndb.StringProperty()
    username = ndb.StringProperty(required=True)
    username_lower = ndb.ComputedProperty(lambda self: self.username.lower())
    password = ndb.StringProperty(required=True)
    email = ndb.StringProperty(required=True)

    # derived name property that either returns dispname or username
    @property
    def name(self):
        if self.dispname:
            return self.dispname
        return self.username


class Article(ndb.Model):
    """Article entity - represents blog article"""
    title = ndb.StringProperty(required=True)
    body = ndb.StringProperty()
    date_time_created = ndb.DateTimeProperty(auto_now_add=True)
    date_time_last_edited = ndb.DateTimeProperty(auto_now=True)
