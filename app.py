import requests
import smtplib
from pprint import pprint
from bs4 import BeautifulSoup
from bs4 import BeautifulSoup as bs
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from requests import Session
from datetime import datetime


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

    home_page = None
    with Session() as s:
        header = {
            "Host": "codingbat.com",
            "Origin": "https://codingbat.com",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        login_data = {"uname": "andre.chmielewski@nbps.org", "pw": "Carambola3993", "dologin": "log in", "fromurl": "/java"}
        s.post("https://codingbat.com/login", data=login_data, headers=header)
        home_page = s.get("https://codingbat.com/report")
        #print(home_page.content)

    with open("/Users/adamhorvitz/PycharmProjects/pythonProject/CodingBat Teacher Report.html") as page:
        soupTest = BeautifulSoup(page, 'html.parser')
        #pprint(soupTest)
        print("PRINTING HERE, READ BELOW")

    soup = BeautifulSoup(home_page.content, 'html.parser')
    #pprint(soup)
    tbody = soup.find_all('table')[2]
    #pprint(tbody)

    emailList = []
    tr = tbody.find_all('tr')
    print("length of tbody is " + str(len(tr)))

    for x in range(2, len(tr)):
        print(tr[x])
        # email = tr.find_all(
        #     "a", string=lambda text: "@" in text.lower()
        # )
        row_data = tr[x].findAll("td")
        print("Row data is " + str(row_data))
        email = row_data[0].findAll(text=True)[0]
        memo = row_data[1].findAll(text=True)
        points = row_data[-1].findAll(text=True)
        # # If the array has a value parse it out and replace the value
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
    pprint(emailList)




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


