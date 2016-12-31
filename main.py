from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for

from google.appengine.ext import ndb

from models import Account, Article

import _main

app = Flask(__name__)
app.config['DEBUG'] = True

# Note: We don't need to call run() since our application is embedded within
# the App Engine WSGI application server.


@app.route('/')
def index():
    """Post new article using a default account each time a page is visited. Stop when article count reaches 10."""
    account = _main._getCurrentAccount()
    account_key = account.key

    articles = []
    q = Article.query(ancestor=account_key)
    q = q.order(-Article.date_time_created)
    articles = q.fetch()

    if len(articles) < 10:
        newArticle = Article(
            parent=account_key,
            title="My Post #%d" % len(articles),
            body="Lorel ipsum!",
            date_time_created=datetime.now(),
            date_time_last_edited=datetime.now())
        newArticle.put()
        articles.insert(0,newArticle)

    return render_template("index.html", title="Hello, world!", account=account, articles=articles)


@app.route('/article/create', methods=['POST'])
def article_create():
    account = _main._getCurrentAccount()
    account_key = account.key

    new_article = Article(
        parent=account_key,
        title=request.form['title'],
        body=request.form['body'],
        date_time_created=datetime.now(),
        date_time_last_edited=datetime.now())
    new_article.put()
    return redirect(url_for('index'))


@app.route('/article/<string:article_key_urlsafe>/edit', methods=['POST'])
def article_edit(article_key_urlsafe):
    article_key = ndb.Key(urlsafe=article_key_urlsafe)
    if not article_key:
        return 'invalid key'

    account = _main._getCurrentAccount()
    if not account:
        return 'not logged in'

    account_key = account.key

    if article_key.parent() != account_key:
        return "cannot edit another person's post"

    article = article_key.get()
    article.title = request.form['title']
    article.body = request.form['body']
    article.date_time_last_edited = datetime.now()
    article.put()

    return redirect(url_for('index'))


@app.route('/article/<string:article_key_urlsafe>/delete', methods=['POST'])
def article_delete(article_key_urlsafe):
    article_key = ndb.Key(urlsafe=article_key_urlsafe)
    if not article_key:
        return 'invalid key'

    account = _main._getCurrentAccount()
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
