from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, make_response

from google.appengine.ext import ndb

from models import Account, Article, Like, Comment

import re
import logging
import _main

app = Flask(__name__)
app.config['DEBUG'] = True
uid = ""

# Note: We don't need to call run() since our application is embedded within
# the App Engine WSGI application server.


@app.route('/blog')
def index():
    """Display all articles from all users"""
    account = _main.get_current_account(request)

    q = Article.query()
    q = q.order(-Article.date_time_created)
    articles = q.fetch()

    return render_template("index.html", title="Hello, world!", account=account, articles=articles)


@app.route('/blog/signup')
def account_signup():
    account = _main.get_current_account(request)
    next = _main.get_redirect_target(request)
    return render_template("signup.html", title="Hello, world!", account=account, next=next)


@app.route('/blog/login', methods=['GET','POST'])
def account_login():
    if request.method == 'GET':
        account = _main.get_current_account(request)
        next = _main.get_redirect_target(request)
        return render_template("login.html", title="Hello, world!", account=account, next=next)
    else:
        username = request.form['username']
        username_lower = username.lower()
        password = request.form['password']
        next_url = request.form['next']
        host_url = request.host_url

        q = Account.query()
        q = q.filter(Account.username_lower==username_lower)
        account = q.get()

        if not account:
            # invalid account name
            return render_template("login.html", title="Hello, world! (invalid act)")

        if not _main.is_hashed_password_valid(username_lower, password, account.password):
            # invalid account password
            return render_template("login.html", title="Hello, world! (invalid pwd)")

        response = make_response(_main.redirect_back(host_url, next_url, url_for('index')))
        _main.login(response, account)
        return response


@app.route('/blog/logout')
def account_logout():
    cur_account = _main.get_current_account(request)

    host_url = request.host_url
    next_url = _main.get_redirect_target(request)

    response = make_response(_main.redirect_back(host_url, next_url, url_for('index')))

    if cur_account:
        _main.logout(response)

    return response


@app.route('/blog/create', methods=['POST'])
def account_create():
    username = request.form['username'].strip()
    username_lower = username.lower()
    dispname = request.form['dispname'].strip()
    password = request.form['password']
    email = request.form['email'].strip().lower()
    next_url = request.form['next'].strip()
    host_url = request.host_url.strip()

    # Since username is used as a part of the URL to access user-specific pages and calls,
    # username must be usable as a URL path.
    # Allow characters specified in RFC3986.
    # However, place additional restrictions pursuant to most of Google Name and Password Guidelines
    # for better compatibility with using usernames as a part of URL paths.
    # Google Name and Password Guidelines
    # Usernames can contain letters (a-z), numbers (0-9), dashes (-), underscores (_), apostrophes ('), and periods (.).
    # Usernames can't contain more than one period (.) in a row.
    # Usernames can begin or end with non-alphanumeric characters except periods (.), with a maximum of 64 characters.
    # Passwords can contain any combination of ASCII characters and must contain a minimum of 8 characters.
    if not username:
        return 'invalid user name. user must be specified.'

    if len(username) > 64:
        return 'invalid user name. user name can be at most 64 characters long.'

    if not re.search("^[a-zA-Z0-9\-\_\'\.]+$", username):
        return 'invalid user name. user name may contain letters (a-z), numbers (0-9), dashes (-), underscores (_), apostrophes (\'), or periods (.).'

    if re.search("^\.", username) or re.match("\.$", username):
        return 'invalid user name. user name cannot start or end with a period (.).'

    if re.search("\.{2,}", username):
        return 'invalid user name. user name cannot contain more than one period (.) in a row.'

    if not password:
        return 'invalid password. password must be specified.'

    if len(password) < 8:
        return 'invalid password. password must be at least 8 characters long.'

    # I will NOT impose any complexity requirements for password.

    # loose verification due to e-mail addresses supporting UTF-8 per RFC6530-6533
    # although verification via confirmation e-mail is not implemented in this system, we can only validate that
    # [1] e-mail address is valid and [2] e-mail address belongs to the person registering by sending
    # a confirmation e-mail to the said address and request the user to click on the
    # verification link.
    # NOTE: technically allowed, but dotless e-mail addresses are strongly discouraged by ICANN
    # per https://www.icann.org/news/announcement-2013-08-30-en
    if not re.search('[^\s@]+@[^\s@]+\.[^\s@]+', email):
        return 'invalid email address. address must include ONE at (@) symbol and AT LEAST ONE dot (.)'

    q = Account.query(Account.username_lower==username_lower)
    account = q.get()

    # username must be unique
    if account:
        return 'account with same username already exists'

    q = Account.query(Account.email==email)
    account = q.get()

    # email must be unique
    if account:
        return 'account with same email address already exists'

    new_account = Account(
        username=username,
        dispname=dispname,
        password=_main.get_hashed_password(username_lower, password),
        email=email
    )
    new_account.put()

    response = make_response(_main.redirect_back(host_url, next_url, url_for('index')))
    _main.login(response, new_account)
    return response


@app.route('/blog/<username>')
def account_view(username):
    """Display articles using current account"""
    username_lower = username.lower()
    q = Account.query(Account.username_lower==username_lower)
    account = q.get()

    if not account:
        return 'invalid account'

    cur_account = _main.get_current_account(request)

    q = Article.query(ancestor=account.key)
    q = q.order(-Article.date_time_created)
    articles = q.fetch()

    return render_template("index.html", title="Hello, world!", account=cur_account, articles=articles)


@app.route('/blog/<username>/article/create', methods=['POST'])
def article_create(username):
    username_lower = username.lower()
    q = Account.query(Account.username_lower==username_lower)
    account = q.get()

    if not account:
        return 'invalid account'

    cur_account = _main.get_current_account(request)

    if account.key != cur_account.key:
        return 'You can only create a new article under your account'

    title = request.form['title']
    body = request.form['body']
    next_url = request.form['next']
    host_url = request.host_url

    new_article = Article(
        parent=account.key,
        title=title,
        body=body)
    new_article.put()

    return _main.redirect_back(host_url, next_url, url_for('index'))


@app.route('/blog/<username>/article/<int:article_id>')
def article_view(username, article_id):
    username_lower = username.lower()
    q = Account.query(Account.username_lower==username_lower)
    account = q.get()

    if not account:
        return 'invalid account'

    article_key = ndb.Key(Account, account.key.id(), Article, article_id)
    if not article_key:
        return 'invalid key'
    article = article_key.get()

    cur_account = _main.get_current_account(request)

    return render_template("article.html", title="Hello, world!", account=cur_account, article=article)


@app.route('/blog/<username>/article/<int:article_id>/edit', methods=['POST'])
def article_edit(username, article_id):
    username_lower = username.lower()
    q = Account.query(Account.username_lower==username_lower)
    account = q.get()

    if not account:
        return 'invalid account'

    article_key = ndb.Key(Account, account.key.id(), Article, article_id)
    if not article_key:
        return 'invalid key'

    cur_account = _main.get_current_account(request)
    if not cur_account:
        return 'not logged in'

    if article_key.parent() != cur_account.key:
        artid = article_key.parent().id()
        curid = cur_account.key.id()
        return "cannot edit another person's post %d / %d" % (artid, curid)

    article = article_key.get()
    article.title = request.form['title']
    article.body = request.form['body']
    article.date_time_last_edited = datetime.now()
    article.put()

    host_url = request.host_url
    next_url = request.form['next']

    return _main.redirect_back(host_url, next_url, url_for('index'))


@app.route('/blog/<username>/article/<int:article_id>/delete', methods=['POST'])
def article_delete(username, article_id):
    username_lower = username.lower()
    q = Account.query(Account.username_lower==username_lower)
    account = q.get()

    if not account:
        return 'invalid account'

    article_key = ndb.Key(Account, account.key.id(), Article, article_id)
    if not article_key:
        return 'invalid key'

    cur_account = _main.get_current_account(request)
    if not cur_account:
        return 'not logged in'

    if article_key.parent() != cur_account.key:
        artid = article_key.parent().id()
        curid = cur_account.key.id()
        return "cannot edit another person's post %d / %d" % (artid, curid)

    if article_key:
        article_key.delete()

    host_url = request.host_url
    next_url = request.form['next']

    return _main.redirect_back(host_url, next_url, url_for('index'))


@app.route('/blog/<username>/article/<int:article_id>/like', methods=['POST'])
def article_like(username, article_id):
    username_lower = username.lower()
    q = Account.query(Account.username_lower==username_lower)
    account = q.get()

    if not account:
        return 'invalid account'

    article_key = ndb.Key(Account, account.key.id(), Article, article_id)
    if not article_key:
        return 'invalid key'

    cur_account = _main.get_current_account(request)
    if not cur_account:
        return 'not logged in'

    if article_key.parent() == cur_account.key:
        return "cannot like your own post"

    q = Like.query(ancestor=article_key)
    q = q.filter(Like.account_key==cur_account.key)
    like = q.get()

    if like:
        like.key.delete()
    else:
        new_like = Like(
            parent=article_key,
            account_key=cur_account.key)
        new_like.put()

    host_url = request.host_url
    next_url = request.form['next']

    return _main.redirect_back(host_url, next_url, url_for('index'))


@app.route('/blog/<username>/article/<int:article_id>/comment/create', methods=['POST'])
def comment_create(username, article_id):
    username_lower = username.lower()
    q = Account.query(Account.username_lower==username_lower)
    account = q.get()

    if not account:
        return 'invalid account'

    article_key = ndb.Key(Account, account.key.id(), Article, article_id)
    if not article_key:
        return 'invalid key'

    cur_account = _main.get_current_account(request)
    if not cur_account:
        return 'not logged in'

    q = Comment.query(ancestor=article_key)
    q = q.order(-Comment.comment_number)
    last_comment = q.get()

    if last_comment:
        last_comment_number = last_comment.comment_number
    else:
        last_comment_number = 0

    title = request.form['title']
    body = request.form['body']
    next_url = request.form['next']
    host_url = request.host_url

    new_comment = Comment(
        parent=article_key,
        comment_number=last_comment_number+1,
        title=title,
        body=body,
        account_key=cur_account.key)
    new_comment.put()

    return _main.redirect_back(host_url, next_url, url_for('index'))


@app.route('/blog/<username>/article/<int:article_id>/comment/<int:comment_number>/edit', methods=['GET','POST'])
def comment_edit(username, article_id, comment_number):
    username_lower = username.lower()
    q = Account.query(Account.username_lower==username_lower)
    account = q.get()

    if not account:
        return 'invalid account'

    article_key = ndb.Key(Account, account.key.id(), Article, article_id)
    if not article_key:
        return 'invalid key'

    cur_account = _main.get_current_account(request)
    if not cur_account:
        return 'not logged in'

    q = Comment.query(ancestor=article_key)
    q = q.filter(Comment.comment_number==comment_number)
    comment = q.get()

    if not comment:
        return 'invalid comment number'

    if comment.account_key != cur_account.key:
        return "cannot edit another person's comment"

    if request.method == 'GET':
        next_url = _main.get_redirect_target(request)
        return render_template("comment-edit.html", title="Hello, world!", account=cur_account, comment=comment, next=next_url)

    else:
        comment.title = request.form['title']
        comment.body = request.form['body']
        comment.put()

        host_url = request.host_url
        next_url = request.form['next']

        return _main.redirect_back(host_url, next_url, url_for('index'))


@app.route('/blog/<username>/article/<int:article_id>/comment/<int:comment_number>/delete', methods=['POST'])
def comment_delete(username, article_id, comment_number):
    username_lower = username.lower()
    q = Account.query(Account.username_lower==username_lower)
    account = q.get()

    if not account:
        return 'invalid account'

    article_key = ndb.Key(Account, account.key.id(), Article, article_id)
    if not article_key:
        return 'invalid key'

    cur_account = _main.get_current_account(request)
    if not cur_account:
        return 'not logged in'

    q = Comment.query(ancestor=article_key)
    q = q.filter(Comment.comment_number==comment_number)
    comment = q.get()

    if not comment:
        return 'invalid comment number'

    if comment.account_key != cur_account.key:
        return "cannot delete another person's comment"

    comment.key.delete()

    host_url = request.host_url
    next_url = request.form['next']

    return _main.redirect_back(host_url, next_url, url_for('index'))


@app.route('/hello')
def hello():
    """Return a friendly HTTP greeting."""
    return render_template("hello.html", title="Hello, world!", text="Hello, world!!")


@app.errorhandler(404)
def page_not_found(e):
    """Return a custom 404 error."""
    return 'Sorry, nothing at this URL.', 404
