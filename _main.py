from datetime import datetime
from urlparse import urlparse, urljoin

from flask import render_template, redirect, url_for

from google.appengine.ext import ndb

from models import Account, Article

import hmac
import logging
import random
import hashlib

HMAC_SECRET = "Attention all aircraft, this is Comona base. This rocket launch is critical. Maintain air superiority until the launch is complete."

def get_current_account(request):
    account_id_secure = request.cookies.get('account_id')
    if account_id_secure:
        if is_secure_value_valid(account_id_secure):
            account_id = int(get_plaintext_value(account_id_secure))
            account = Account.get_by_id(account_id)
            if account:
                return account
    return None

def get_secure_value(value):
    return "%s|%s" % (value, hmac.new(HMAC_SECRET, value).hexdigest())

def get_plaintext_value(secure_value):
    return secure_value.split("|")[0]

def is_secure_value_valid(secure_value):
    value = get_plaintext_value(secure_value)
    return secure_value == get_secure_value(value)

def get_salt():
    r = random.SystemRandom()
    return "".join([str(chr(r.randrange(33, 126, 1))) for i in range(5)])

def get_hashed_password(name, pw, salt = None):
    if not salt:
        salt = get_salt()
    hash = hashlib.sha256(name + pw + salt).hexdigest()
    return "%s|%s" % (salt, hash)

def is_hashed_password_valid(name, password, hashed_password):
    salt = hashed_password.split("|")[0]
    return hashed_password == get_hashed_password(name, password, salt)

def set_secure_cookie(response,key,value):
    response.set_cookie(key, get_secure_value(value))
    return response

def is_secure_cookie_valid(request,key):
    secure_value = request.cookies.get(key)
    if secure_value:
        return is_secure_value_valid(secure_value)
    else:
        return None

def login(response,account):
    set_secure_cookie(response,"account_id",str(account.key.id()))

def logout(response):
    response.set_cookie("account_id","")

# adapted from Securely Redirect Back by Armin Ronacher
# http://flask.pocoo.org/snippets/62/
def is_safe_url(host_url,target_url):
    ref_url = urlparse(host_url)
    tst_url = urlparse(urljoin(host_url,target_url))
    is_http = tst_url.scheme in ('http','https')
    is_host_same = ref_url.netloc == tst_url.netloc
    return is_http and is_host_same

def get_redirect_target(request):
    for next_url in request.values.get('next'), request.referrer:
        if not next_url:
            continue
        if is_safe_url(request.host_url, next_url):
            return next_url

# Inputs will typically come from...
# host_url = request.host_url
# target_url = request.form['next']
# default_url = url_for('somedefaulturl',param1,param2...)
def redirect_back(host_url, next_url, default_url):
    if next_url and is_safe_url(host_url, next_url):
        redirect_url = next_url
    else:
        redirect_url = default_url
    return redirect(redirect_url)
