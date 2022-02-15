from dotenv import load_dotenv
from os import environ
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from requests import Session
import time
from datetime import datetime, date
from flask_apscheduler import APScheduler
from flask_login import LoginManager, UserMixin, login_required, logout_user, current_user, login_user
from flask_migrate import Migrate

from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
load_dotenv()

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = environ.get('SQLALCHEMY_DATABASE_URI')
# app.config['SQLALCHEMY_DATABASE_URI'] = environ.get('DATABASE_URL')
db = SQLAlchemy(app)
app.secret_key = environ.get('APP_SECRET_KEY')

login_manager = LoginManager()
login_manager.init_app(app)

migrate = Migrate(app, db)


@app.before_first_request
def before_first_request():
    try:
        Frequency.query.all()
    except:
        db.create_all()
        frequency = Frequency()
        db.session.add(frequency)
        db.session.commit()

    try:
        User.query.all()
    except:
        db.create_all()


class Frequency(db.Model):
    frequency = db.Column(db.Integer, default=1, primary_key=True)

    def __repr__(self):
        return str(self.frequency)


class User(UserMixin, db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    # name = db.Column(
    #     db.String(100),
    #     nullable=False,
    #     unique=False
    # )
    email = db.Column(
        db.String(40),
        unique=True,
        nullable=False
    )
    password = db.Column(
        db.String(200),
        primary_key=False,
        unique=False,
        nullable=False
    )
    codingbat_email = db.Column(
        db.String(40),
        unique=False,
        nullable=True,
        default="andre.chmielewski@nbps.org"
    )
    codingbat_password = db.Column(
        db.String(200),
        unique=False,
        primary_key=False,
        nullable=True,
        default="Carambola3993"
    )


    def set_password(self, password):
        """Create hashed password."""
        self.password = generate_password_hash(
            password,
            method='sha256'
        )

    def check_password(self, password):
        """Check hashed password."""
        return check_password_hash(self.password, password)

    def __repr__(self):
        return '<User {}>'.format(self.username)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


@login_manager.unauthorized_handler
def unauthorized():
    flash("You must be logged in to view that page.")
    return redirect(url_for("login"))


class Config:
    SCHEDULER_API_ENABLED = True
    SCHEDULER_TIMEZONE = "America/New_York"


app.config.from_object(Config())

scheduler = APScheduler()
# scheduler.add_job(func=database, trigger="interval", days=7)
scheduler.init_app(app)
scheduler.start()

try:
    Frequency.query.all()
except:
    db.create_all()
    frequency = Frequency()
    db.session.add(frequency)
    db.session.commit()


frequency = Frequency.query.first()


@scheduler.task('interval', id='database', days=frequency.frequency, misfire_grace_time=900)
def database():
    user = User.query.order_by(User.id.desc()).first()
    username = user.codingbat_email
    password = user.codingbat_password

    home_page = None
    with Session() as s:
        header = {
            "Host": "codingbat.com",
            "Origin": "https://codingbat.com",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        login_data = {"uname": username, "pw": password, "dologin": "log in",
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

    last_scrape_entry = Scrape.query.order_by(Scrape.date.desc()).first()
    # print("Last scrape entry date is " + str(last_scrape_entry.date) + " and today's date is " + str(date.today()))
    # print(last_scrape_entry is None or (last_scrape_entry is not None and last_scrape_entry.date != date.today()))
    if last_scrape_entry is None or (last_scrape_entry is not None and last_scrape_entry.date != date.today()):
        print("RUNNING DATABASE")
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

        # flash("Database updated.")
        db.session.commit()
        ranking()
        change_in_points()
        # pprint(emailList)


def date_deleter():
    date = Scrape.query.order_by(Scrape.date.desc()).first().date
    scrapes = Scrape.query.filter_by(date=date).all()

    for scrape in scrapes:
        db.session.delete(scrape)

    db.session.commit()


# def rank_all():
#     # date_deleter()  # Delete the most recent date (debug)
#
#     # Get all scrapes in the database
#     scrapes = Scrape.query.all()
#
#     # Go through each scrape and extract ALL the dates
#     dates = set()
#     for scrape in scrapes:
#         dates.add(scrape.date)
#     print(dates)

def change_in_points():
    students = Student.query.all()
    studentChange = 0

    for student in students:
        studentPoints = []
        scrapes = Scrape.query.order_by(Scrape.date.desc()).filter_by(student_id=student.id).all()
        # Order the scrapes for each student from most recent date to last
        for scrape in scrapes:
            studentPoints.append(scrape.points)
            # print(studentPoints)
            # Calculate the difference from current scrape and the one before
            if len(studentPoints) != 1:
                for x in range(0, 1):
                    # print(studentPoints[x])
                    change = studentPoints[x] - studentPoints[x - 1]
                    # print(change)
                scrape.change = change
                db.session.add(scrape)
            else:
                scrape.change = 0

    db.session.commit()


def ranking():
    # scrapes = Scrape.query.filter_by(date=date).all()

    date = Scrape.query.order_by(Scrape.date.desc()).first().date
    scrapes = Scrape.query.order_by(Scrape.points.desc()).filter_by(date=date).all()
    ranking = 1
    for scrape in scrapes:
        scrape.ranking = ranking
        db.session.add(scrape)
        # print(ranking)
        ranking += 1

    db.session.commit()


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

    isArchived = db.Column(db.Boolean, default=False)

    scrapes = db.relationship('Scrape', backref='student', lazy=False)

    def __repr__(self):
        return '<Student %r>' % self.id


class Scrape(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    points = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, default=date.today())
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    change = db.Column(db.Integer, nullable=True)

    # student = db.relationship('Student', backref=db.backref('students', lazy=True))

    def __repr__(self):
        return '<Scrape %r>' % self.id


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True, autoincrement=True)

    def __repr__(self):
        return '<Category %r>' % self.name


@app.route('/', methods=['GET', 'POST'])
def login():  # put application's code here
    if request.method == 'GET':
        if current_user.is_authenticated:
            return redirect(url_for('view_posts'))
        return render_template("login.html")
    else:
        email = request.form["email"]
        user = User.query.filter_by(email=email).first()
        password = request.form["password"]
        if user and user.check_password(password=password):  # If the user exists and the password is correct
            login_user(user)
            flash("Login successful.")
            return redirect(url_for("view_posts"))
        flash("Login unsuccessful. Please try again or create a new account.")
        return redirect(url_for("login"))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == "GET":
        if current_user.is_authenticated:
            return redirect(url_for('view_posts'))

    else:
        # Logic for creating a new user, then logging them in
        email = request.form["email"]
        existing_user = User.query.filter_by(email=email).first()
        if existing_user is None:
            user = User(email=email)
            user.set_password(request.form["password"])
            db.session.add(user)
            db.session.commit()
            login_user(user)
            database()
            return redirect(url_for("view_posts"))
        flash("A user with that email already exists.")
    return render_template("signup.html")


@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == "GET":
        frequency = Frequency.query.first().frequency
        user = User.query.filter_by(id=current_user.id).first()
        username = user.codingbat_email
        password = user.codingbat_password
        return render_template("/settings.html", username=username, password=password, frequency=frequency)
    else:
        fetched_frequency = request.form["frequency"]
        fetched_username = request.form["username"]
        fetched_password = request.form["password"]

        user = User.query.filter_by(id=current_user.id).first()
        frequency = Frequency.query.first()

        if fetched_frequency == "month":
            frequency.frequency = 30
        elif fetched_frequency == "week":
            frequency.frequency = 7
        else:
            frequency.frequency = 1
        flash("Frequency updated to every " + str(frequency.frequency) + " day(s)")

        scheduler.add_job(
            func=database,
            trigger="interval",
            days=frequency.frequency,
            id="database",
            name="database",
            replace_existing=True,
        )
        # job = scheduler.get_job("database")
        # flash(job.trigger)
        # scheduler.reschedule_job('database', trigger='cron', days=frequency.frequency)

        if fetched_username == "" or fetched_password == "":
            flash("Username/password values not changed")
        else:
            flash("Username/password values changed")
            user.codingbat_email = fetched_username
            user.codingbat_password = fetched_password

        username = user.codingbat_email
        password = user.codingbat_password
        db.session.commit()

        return render_template("/settings.html", username=username, password=password, frequency=frequency)


@app.route('/database', methods=['GET', 'POST'])
@login_required
def view_posts():
    if request.method == "GET":
        # # print("opening database.html")
        # database()
        try:
            students = Student.query.all()
            date = Scrape.query.order_by(Scrape.date.desc()).first().date
        except:
            database()
            print('Running exception')
            students = Student.query.all()
            date = Scrape.query.order_by(Scrape.date.desc()).first().date
        # print("Most recent scrape is from " + str(date))
        scrapes = Scrape.query.filter_by(date=date).all()
        # print(scrapes[0].student.id)
        return render_template("database.html", posts=students, scrapes=scrapes)


@app.route('/database/archive', methods=['GET', 'POST'])
@login_required
def view_archived():
    if request.method == "GET":
        students = Student.query.all()
        date = Scrape.query.order_by(Scrape.date.desc()).first().date
        scrapes = Scrape.query.filter_by(date=date).all()
        return render_template("archive-database.html", posts=students, scrapes=scrapes)


@app.route('/database/points', methods=['GET', 'POST'])
@login_required
def points():
    if request.method == "GET":
        # database()
        students = Student.query.all()
        # points = Scrape.query.order_by(Scrape.points).first().points
        date = Scrape.query.order_by(Scrape.date.desc()).first().date
        scrapes = Scrape.query.order_by(Scrape.points.desc()).filter_by(date=date).all()

        return render_template("database.html", posts=students, scrapes=scrapes)


@app.route('/database/change', methods=['GET', 'POST'])
@login_required
def change():
    if request.method == "GET":
        # database()
        students = Student.query.all()
        # points = Scrape.query.order_by(Scrape.points).first().points
        date = Scrape.query.order_by(Scrape.date.desc()).first().date
        scrapes = Scrape.query.order_by(Scrape.change.desc()).filter_by(date=date).all()

        return render_template("database.html", posts=students, scrapes=scrapes)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out.")
    return redirect(url_for("login"))


@app.route('/student/<int:scrape_student_id>', methods=['GET', 'POST'])
@login_required
def display_student(scrape_student_id):
    fetched_student = Student.query.get(scrape_student_id)
    scrapes = Scrape.query.filter_by(student_id=scrape_student_id).order_by(Scrape.date.desc()).all()
    return render_template("/student.html", student=fetched_student, scrapes=scrapes)


@app.route('/student/<int:student_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_student(student_id):
    if request.method == "GET":
        fetched_student = Student.query.get(student_id)
        scrapes = Scrape.query.filter_by(student_id=student_id).order_by(Scrape.date.desc()).all()
        return render_template("/student-edit.html", student=fetched_student, scrapes=scrapes)
    else:
        fetched_student = Student.query.get(student_id)
        fetched_student.email = request.form["email"]
        fetched_student.grade = request.form["grade"]
        fetched_student.gradYear = request.form["gradYear"]
        fetched_student.period = request.form["period"]
        fetched_student.theClass = request.form["class"]
        isBoolean = request.form["isArchived"]
        if isBoolean == "True" or isBoolean == "False":
            fetched_student.isArchived = eval(isBoolean)
        flash("Student info updated.")
        db.session.commit()

        scrapes = Scrape.query.filter_by(student_id=student_id).order_by(Scrape.date.desc()).all()
        return render_template("/student.html", student=fetched_student, scrapes=scrapes)


if __name__ == '__main__':
    # rank_all()
    # db.drop_all()
    db.create_all()
    # date_deleter()
    # database()
    # change_in_points()
    app.run(debug=True)
