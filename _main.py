from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for

from google.appengine.ext import ndb

from models import Account, Article

import hmac
import logging
import random
import hashlib

HMAC_SECRET = "Attention all aircraft, this is Comona base. This rocket launch is critical. Maintain air superiority until the launch is complete."

def _get_current_account(request):
    account_id_secure = request.cookies.get('account_id')
    if account_id_secure:
        if _is_secure_value_valid(account_id_secure):
            account_id = int(_get_plaintext_value(account_id_secure))
            account = Account.get_by_id(account_id)
            if account:
                return account
    return None

def _get_secure_value(value):
    return "%s|%s" % (value, hmac.new(HMAC_SECRET, value).hexdigest())

def _get_plaintext_value(secure_value):
    return secure_value.split("|")[0]

def _is_secure_value_valid(secure_value):
    value = _get_plaintext_value(secure_value)
    return secure_value == _get_secure_value(value)

def _get_salt():
    r = random.SystemRandom()
    return "".join([str(chr(r.randrange(33, 126, 1))) for i in range(5)])

def _get_hashed_password(name, pw, salt = None):
    if not salt:
        salt = _get_salt()
    hash = hashlib.sha256(name + pw + salt).hexdigest()
    return "%s|%s" % (salt, hash)

def _is_hashed_password_valid(name, password, hashed_password):
    salt = hashed_password.split("|")[0]
    return hashed_password == _get_hashed_password(name, password, salt)

def _set_secure_cookie(response,key,value):
    response.set_cookie(key, _get_secure_value(value))
    return response

def _is_secure_cookie_valid(request,key):
    secure_value = request.cookies.get(key)
    if secure_value:
        return _is_secure_value_valid(secure_value)
    else:
        return None

def _login(response,account):
    _set_secure_cookie(response,"account_id",str(account.key.id()))

def _logout(response):
    response.set_cookie("account_id","")

