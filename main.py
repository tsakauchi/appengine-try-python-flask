from datetime import datetime

from flask import Flask, render_template

from google.appengine.ext import ndb

from models import Account, Article

app = Flask(__name__)
app.config['DEBUG'] = True

# Note: We don't need to call run() since our application is embedded within
# the App Engine WSGI application server.


@app.route('/')
def index():
    """Post new article using a default account each time a page is visited. Stop when article count reaches 10."""
    q = Account.query()
    q = q.filter(Account.name == "Dev Blog")
    account = q.get()

    if account:
        account_key = account.key
    else:
        account = Account(
            name="Dev Blog",
            password="dev",
            email="dev@blog.com")
        account_key = account.put()

    articles = []

    q = Article.query()
    q = q.filter(Article.account_key == account_key)
    q = q.order(Article.date_time_last_edited)
    articles = q.fetch()

    if len(articles) < 10:
        newArticle = Article(
            title="My Post #%d" % len(articles),
            body="Lorel ipsum!",
            date_time_created=datetime.now(),
            date_time_last_edited=datetime.now(),
            account_key=account_key)
        newArticle.put()
        articles.append(newArticle)

    return render_template("index.html", title="Hello, world!", text="Hello, world!!", articles=articles)


@app.route('/hello')
def hello():
    """Return a friendly HTTP greeting."""
    return render_template("hello.html", title="Hello, world!", text="Hello, world!!")


@app.errorhandler(404)
def page_not_found(e):
    """Return a custom 404 error."""
    return 'Sorry, nothing at this URL.', 404
