from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for

from google.appengine.ext import ndb

from models import Account, Article

def _getCurrentAccount():
    """Get account entity of the account that is currently logged in"""
    q = Account.query()
    q = q.filter(Account.email == "dev@blog.com")
    account = q.get()

    if not account:
        account = Account(
            name="Dev Blog",
            password="dev",
            email="dev@blog.com")
        account.put()

    return account
