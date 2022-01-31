import requests
import smtplib
from pprint import pprint
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from requests import Session
import time
import atexit
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, date

app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
db = SQLAlchemy(app)
app.secret_key = 'the random string'


@app.before_first_request
def create_tables():
    db.create_all()


def database():
    # db.drop_all()
    db.create_all()

    # todayDate = Scrape.query.order_by(Scrape.date).first().date
    # print(date)
    # if todayDate != date.today() or todayDate is None:
    home_page = None
    with Session() as s:
        header = {
            "Host": "codingbat.com",
            "Origin": "https://codingbat.com",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        login_data = {"uname": "andre.chmielewski@nbps.org", "pw": "Carambola3993", "dologin": "log in",
                      "fromurl": "/java"}
        s.post("https://codingbat.com/login", data=login_data, headers=header)
        home_page = s.get("https://codingbat.com/report")
        # print(home_page.content)

    # with app.open_resource('static/CodingBat Teacher Report.html') as page:
    #     soup = BeautifulSoup(page, 'html.parser')
    #       #pprint(soupTest)

    soup = BeautifulSoup(home_page.content, 'html.parser')
    # pprint(soup)
    tbody = soup.find_all('table')[2]
    # pprint(tbody)

    emailList = []
    tr = tbody.find_all('tr')
    # print("length of tbody is " + str(len(tr)))

    last_scrape_entry = Scrape.query.order_by(Scrape.date).first()
    if last_scrape_entry is None or (last_scrape_entry is not None and last_scrape_entry.date != date.today()):
        for x in range(2, len(tr)):
            # print(tr[x])
            # email = tr.find_all(
            #     "a", string=lambda text: "@" in text.lower()
            # )
            row_data = tr[x].findAll("td")
            # print("Row data is " + str(row_data))
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

            # 1. Check if the student already exists in the Student table
            student = Student.query.filter_by(email=email).first()

            if student is None:
                # 2. If doesn't exist, create a new student object with email and memo, and save ID as a variable
                student = Student(
                    email=email,
                    memo=memo
                    # id=x-2
                )

            # 3. If it already exists, save the ID as a variable

            # 4. Create the Scrape object with date, points, and Student_ID
            scrape = Scrape(
                student=student,
                points=points
            )
            # print(scrape)

            # 5. Commit and add to database

            # pprint(student.email + ", " + student.memo + ", " + str(student.points) + ", " + str(student.date))
            # db.session.add(student)
            db.session.add(scrape)
            emailList.append([email, memo, points])

        db.session.commit()
        # pprint(emailList)


def print_date_time():
    print(time.strftime("%A, %d. %B %Y %I:%M:%S %p"))


class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False)
    memo = db.Column(db.String(255), nullable=False)

    grade = db.Column(db.Integer, default=9)
    gradYear = db.Column(db.Integer, default=2026)
    theClass = db.Column(db.String(255), default="AP Computer Science A")
    period = db.Column(db.Integer, default=1)

    scrapes = db.relationship('Scrape', backref='student', lazy=False)

    def __repr__(self):
        return '<Student %r>' % self.id


class Scrape(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    points = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, default=date.today())
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=True)

    # student = db.relationship('Student', backref=db.backref('students', lazy=True))

    def __repr__(self):
        return '<Scrape %r>' % self.id


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True, autoincrement=True)

    def __repr__(self):
        return '<Category %r>' % self.name


@app.route('/')
def index():  # put application's code here
    return render_template("index.html")


@app.route('/settings', methods=['GET', 'POST'])
def settings():
    return render_template("/settings.html")


@app.route('/database', methods=['GET', 'POST'])
def view_posts():
    if request.method == "GET":
        # # print("opening database.html")
        # database()
        students = Student.query.all()
        date = Scrape.query.order_by(Scrape.date).first().date
        scrapes = Scrape.query.filter_by(date=date).all()
        # print(scrapes[0].student.id)
        return render_template("database.html", posts=students, scrapes=scrapes)


@app.route('/database/points', methods=['GET', 'POST'])
def points():
    if request.method == "GET":
        # database()
        students = Student.query.all()
        # points = Scrape.query.order_by(Scrape.points).first().points
        date = Scrape.query.order_by(Scrape.date).first().date
        scrapes = Scrape.query.order_by(Scrape.points.desc()).filter_by(date=date).all()

        return render_template("database.html", posts=students, scrapes=scrapes)


@app.route('/database/change', methods=['GET', 'POST'])
def change():
    if request.method == "GET":
        # database()
        students = Student.query.all()
        # points = Scrape.query.order_by(Scrape.points).first().points
        date = Scrape.query.order_by(Scrape.date).first().date
        scrapes = Scrape.query.order_by(Scrape.points.desc()).filter_by(date=date).all()

        return render_template("database.html", posts=students, scrapes=scrapes)


@app.route('/student/<int:scrape_student_id>', methods=['GET', 'POST'])
def display_student(scrape_student_id):
    if request.method == "GET":
        fetched_student = Student.query.get(scrape_student_id)
        scrapes = Scrape.query.filter_by(id=scrape_student_id).all()
        return render_template("/student.html", student=fetched_student, scrapes=scrapes)
    else:
        fetched_student = Student.query.get(scrape_student_id)

        fetched_student.email = request.form["email"]
        fetched_student.grade = request.form["grade"]
        fetched_student.gradYear = request.form["gradYear"]
        fetched_student.period = request.form["period"]
        fetched_student.theClass = request.form["class"]
        db.session.commit()

        scrapes = Scrape.query.filter_by(id=scrape_student_id).all()
        return render_template("/student.html", student=fetched_student, scrapes=scrapes)


scheduler = BackgroundScheduler()
scheduler.add_job(func=database, trigger="interval", days=7)
scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())

if __name__ == '__main__':
    # db.drop_all()
    db.create_all()
    app.run(debug=True)
    database()
