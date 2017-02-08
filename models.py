from datetime import datetime
from google.appengine.ext import ndb


class NdbModelBase(ndb.Model):

    # adapted from response to "efficient human readable timedelta"
    # http://codereview.stackexchange.com/a/37286
    def _get_elapsed_time_summary(self, datetimeToGetElapsedTimeFrom):
        elapsedTime = datetime.now() - datetimeToGetElapsedTimeFrom

        days, rem = divmod(elapsedTime.seconds, 86400)
        hours, rem = divmod(rem, 3600)
        minutes, seconds = divmod(rem, 60)
        if seconds < 1:
            seconds = 1
        locals_ = locals()
        magnitudes_str = ("{n} {magnitude}".format(n=int(locals_[magnitude]), magnitude=magnitude)
                          for magnitude in ("days", "hours", "minutes", "seconds") if locals_[magnitude])

        #delta_str = ", ".join(magnitudes_str)
        #return delta_str

        # I just want the most significant magnitude to be shown
        return list(magnitudes_str)[0]


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


class Article(NdbModelBase):
    """Article entity - represents blog article"""
    title = ndb.StringProperty(required=True)
    body = ndb.StringProperty()
    date_time_created = ndb.DateTimeProperty(auto_now_add=True)
    date_time_last_edited = ndb.DateTimeProperty(auto_now=True)

    @property
    def like_count(self):
        q = Like.query(ancestor=self.key)
        likes = q.fetch()
        return len(likes)

    def is_account_liked_article(self, account):
        q = Like.query(ancestor=self.key)
        q = q.filter(Like.account_key==account.key)
        like = q.get()
        if like:
            return True
        else:
            return False

    @property
    def delta_created(self):
        return self._get_elapsed_time_summary(self.date_time_created)

    @property
    def delta_last_edited(self):
        created_vs_edited = self.date_time_created - self.date_time_last_edited
        if created_vs_edited.seconds > 1:
            return self._get_elapsed_time_summary(self.date_time_last_edited)
        return None


class Like(ndb.Model):
    """Like entity - represents like votes. parent is Article entity"""
    account_key = ndb.KeyProperty(required=True, kind=Account)
