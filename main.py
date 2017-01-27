from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, make_response

from google.appengine.ext import ndb

from models import Account, Article

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
    return render_template("signup.html", title="Hello, world!")


@app.route('/blog/login', methods=['GET','POST'])
def account_login():
    if request.method == 'GET':
        return render_template("login.html", title="Hello, world!")
    else:
        username = request.form['username']
        password = request.form['password']

        q = Account.query()
        q = q.filter(Account.name ==username)
        account = q.get()

        if not account:
            # invalid account name
            return render_template("login.html", title="Hello, world! (invalid act)")

        if not _main._is_hashed_password_valid(username, password, account.password):
            # invalid account password
            return render_template("login.html", title="Hello, world! (invalid pwd)")

        response = make_response(redirect(url_for('index')))
        _main._login(response, account)
        return response


@app.route('/blog/create', methods=['POST'])
def account_create():
    new_account = Account(
        name=request.form['name'],
        password=_main._get_hashed_password(request.form['name'], request.form['password']),
        email=request.form['email']
    )
    new_account.put()
    response = make_response(redirect(url_for('index')))
    _main._login(response, new_account)
    return response


@app.route('/blog/<int:account_id>')
def account_view(account_id):
    """Display articles using current account"""
    account_key = ndb.Key(Account, account_id)
    account = account_key.get()

    if account_key:
        q = Article.query(ancestor=account_key)
    else:
        q = Article.query()

    q = q.order(-Article.date_time_created)
    articles = q.fetch()

    return render_template("index.html", title="Hello, world!", account=account, articles=articles)


@app.route('/blog/<int:account_id>/article/create', methods=['POST'])
def article_create(account_id):
    account_key = ndb.Key(Account, account_id)

    cur_account = _main._get_current_account(request)
    cur_account_key = cur_account.key

    if account_key != cur_account_key:
        return 'You can only create a new article under your account'

    new_article = Article(
        parent=account_key,
        title=request.form['title'],
        body=request.form['body'])
    new_article.put()
    return redirect(url_for('index'))


@app.route('/blog/<int:account_id>/article/<int:article_id>')
def article_view(account_id, article_id):
    article_key = ndb.Key(Account, account_id, Article, article_id)
    if not article_key:
        return 'invalid key'
    article = article_key.get()

    account = _main._get_current_account(request)

    return render_template("article.html", title="Hello, world!", account=account, article=article)


@app.route('/blog/<int:account_id>/article/<int:article_id>/edit', methods=['POST'])
def article_edit(account_id, article_id):
    article_key = ndb.Key(Account, account_id, Article, article_id)
    if not article_key:
        return 'invalid key'

    account = _main._get_current_account(request)
    if not account:
        return 'not logged in'

    account_key = account.key

    if article_key.parent() != account_key:
        artid = article_key.parent().id()
        actid = account_key.id()
        return "cannot edit another person's post %d / %d" % (article_key.parent().id(), account_key.id())

    article = article_key.get()
    article.title = request.form['title']
    article.body = request.form['body']
    article.date_time_last_edited = datetime.now()
    article.put()

    return redirect(url_for('index'))


@app.route('/blog/<int:account_id>/article/<int:article_id>/delete', methods=['POST'])
def article_delete(account_id, article_id):
    article_key = ndb.Key(Account, account_id, Article, article_id)
    if not article_key:
        return 'invalid key'

    account = _main._get_current_account(request)
    if not account:
        return 'not logged in'

    account_key = account.key

    if article_key.parent() != account_key:
        return "cannot delete another person's post"

    if article_key:
        article_key.delete()
    return redirect(url_for('index'))


@app.route('/hello')
def hello():
    """Return a friendly HTTP greeting."""
    return render_template("hello.html", title="Hello, world!", text="Hello, world!!")


@app.errorhandler(404)
def page_not_found(e):
    """Return a custom 404 error."""
    return 'Sorry, nothing at this URL.', 404
