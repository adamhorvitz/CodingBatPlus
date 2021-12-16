import requests
import smtplib
from pprint import pprint
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import mechanize
import urllib3
import http.cookiejar ## http.cookiejar in python3

cj = http.cookiejar.CookieJar()
br = mechanize.Browser()
br.set_cookiejar(cj)
br.open("https://www.codingbat.com")

br.select_form(nr=0)
print(mechanize.HTMLForm)
for field_name in br.forms():
    print("field name: ")
    print(field_name)



br.form['uname'] = 'username'
br.form['pw'] = 'password.'
br.submit()
print(br.response().read())

app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
db = SQLAlchemy(app)
app.secret_key = 'the random string'

@app.before_first_request
def create_tables():
    db.create_all()

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    points = db.Column(db.Float, nullable=False)
    email = db.Column(db.String(255), nullable=False)
    memo = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return '<Post %r>' % self.title

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True, autoincrement=True)

    def __repr__(self):
        return '<Category %r>' % self.name


def database():
    db.drop_all()
    db.create_all()
    with open("/Users/adamhorvitz/PycharmProjects/pythonProject/CodingBat Teacher Report.html") as page:
        soup = BeautifulSoup(page, 'html.parser')
    print("running database method!")
    tbody = soup.find_all('tbody')[2]

    emailList = []
    for x in range(2, len(tbody) - 2):
        tr = tbody.find_all('tr')[x]
        # email = tr.find_all(
        #     "a", string=lambda text: "@" in text.lower()
        # )
        row_data = tr.findAll("td")
        email = row_data[0].findAll(text=True)[0]
        memo = row_data[1].findAll(text=True)
        points = row_data[-1].findAll(text=True)
        # If the array has a value parse it out and replace the value
        if len(memo) == 0:
            memo = "No Memo"
        else:
            memo = memo[0]

        if len(points) != 0:
            points = float(points[0])
        # Else replace the value with 0
        else:
            points = 0.0

        post = Post(
            email=email,
            memo=memo,
            points=points
        )
        db.session.add(post)
        # db.session.commit()
        emailList.append([email, memo, points])

    db.session.commit()
    # pprint(emailList)




@app.route('/')
def index():  # put application's code here
    return render_template("index.html")

@app.route('/settings', methods=['GET', 'POST'])
def settings():
        return render_template("/settings.html")


@app.route('/database', methods=['GET', 'POST'])
def view_posts():
    print("opening database.html")
    database()
    posts = Post.query.all()
    return render_template("database.html", posts=posts)



if __name__ == '__main__':
    db.drop_all()
    db.create_all()
    app.run(debug=True)


