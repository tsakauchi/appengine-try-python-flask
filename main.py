from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, make_response

from google.appengine.ext import ndb

from models import Account, Article, Like

import _main

app = Flask(__name__)
app.config['DEBUG'] = True
uid = ""

# Note: We don't need to call run() since our application is embedded within
# the App Engine WSGI application server.


@app.route('/blog')
def index():
    """Display all articles from all users"""
    account = _main._get_current_account(request)

    q = Article.query()
    q = q.order(-Article.date_time_created)
    articles = q.fetch()

    return render_template("index.html", title="Hello, world!", account=account, articles=articles)


@app.route('/blog/signup')
def account_signup():
    account = _main._get_current_account(request)
    return render_template("signup.html", title="Hello, world!", account=account)


@app.route('/blog/login', methods=['GET','POST'])
def account_login():
    if request.method == 'GET':
        account = _main._get_current_account(request)
        return render_template("login.html", title="Hello, world!", account=account)
    else:
        username = request.form['username']
        password = request.form['password']

        username_lower = username.lower()

        q = Account.query()
        q = q.filter(Account.username_lower==username_lower)
        account = q.get()

        if not account:
            # invalid account name
            return render_template("login.html", title="Hello, world! (invalid act)")

        if not _main._is_hashed_password_valid(username_lower, password, account.password):
            # invalid account password
            return render_template("login.html", title="Hello, world! (invalid pwd)")

        response = make_response(redirect(url_for('index')))
        _main._login(response, account)
        return response


@app.route('/blog/logout')
def account_logout():
    cur_account = _main._get_current_account(request)

    response = make_response(redirect(url_for('index')))

    if cur_account:
        _main._logout(response)

    return response


@app.route('/blog/create', methods=['POST'])
def account_create():
    username = request.form['username']
    username_lower = username.lower()

    q = Account.query(Account.username_lower==username_lower)
    account = q.get()

    if account:
        return 'account with same username already exists'

    new_account = Account(
        username=request.form['username'],
        dispname=request.form['dispname'],
        password=_main._get_hashed_password(request.form['username'].lower(), request.form['password']),
        email=request.form['email']
    )
    new_account.put()
    response = make_response(redirect(url_for('index')))
    _main._login(response, new_account)
    return response


@app.route('/blog/<username>')
def account_view(username):
    """Display articles using current account"""
    username_lower = username.lower()
    q = Account.query(Account.username_lower==username_lower)
    account = q.get()

    if not account:
        return 'invalid account'

    cur_account = _main._get_current_account(request)

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

    cur_account = _main._get_current_account(request)

    if account.key != cur_account.key:
        return 'You can only create a new article under your account'

    new_article = Article(
        parent=account.key,
        title=request.form['title'],
        body=request.form['body'])
    new_article.put()

    #return redirect(url_for('index'))
    return redirect(url_for('account_view', username=username_lower))


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

    cur_account = _main._get_current_account(request)

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

    cur_account = _main._get_current_account(request)
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

    #return redirect(url_for('index'))
    return redirect(url_for('account_view', username=username_lower))


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

    cur_account = _main._get_current_account(request)
    if not cur_account:
        return 'not logged in'

    if article_key.parent() != cur_account.key:
        artid = article_key.parent().id()
        curid = cur_account.key.id()
        return "cannot edit another person's post %d / %d" % (artid, curid)

    if article_key:
        article_key.delete()

    #return redirect(url_for('index'))
    return redirect(url_for('account_view', username=username_lower))


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

    cur_account = _main._get_current_account(request)
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

    return redirect(url_for('account_view', username=username_lower))


@app.route('/hello')
def hello():
    """Return a friendly HTTP greeting."""
    return render_template("hello.html", title="Hello, world!", text="Hello, world!!")


@app.errorhandler(404)
def page_not_found(e):
    """Return a custom 404 error."""
    return 'Sorry, nothing at this URL.', 404
