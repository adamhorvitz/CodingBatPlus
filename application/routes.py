from flask import Blueprint
from flask import current_app as app
import matplotlib.pyplot as plt
import mpld3
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_required, logout_user, current_user, login_user
from .models import User, Frequency, Student, Scrape
from .scheduler import database, scheduler, frequency
from . import db
from .functions import send_student_email_reports, send_teacher_email_reports

# Blueprint Configuration
app_bp = Blueprint(
    'app_bp', __name__,
    template_folder='templates',
    static_folder='static'
)


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

    frequency = Frequency.query.first()


@app_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == "GET":
        frequency = Frequency.query.first().frequency
        user = User.query.filter_by(id=current_user.id).first()
        username = user.codingbat_email
        password = user.codingbat_password
        return render_template("/settings.html", username=username, password=password, frequency=frequency, user=user)
    else:
        fetched_frequency = request.form["frequency"]

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
        db.session.commit()

        username = user.codingbat_email
        password = user.codingbat_password

        return render_template("/settings.html", username=username, password=password, frequency=frequency, user=user)


@app_bp.route('/settings/login', methods=['GET', 'POST'])
@login_required
def settings_login():
    if request.method == "GET":
        return redirect(url_for("app_bp.settings"))
    else:
        fetched_username = request.form["username"]
        fetched_password = request.form["password"]
        user = User.query.filter_by(id=current_user.id).first()

        if fetched_username == "" or fetched_password == "":
            flash("Username/password values not changed")
        else:
            flash("Username/password values changed")
            user.codingbat_email = fetched_username
            user.codingbat_password = fetched_password

        username = user.codingbat_email
        password = user.codingbat_password
        db.session.commit()
        frequency = Frequency.query.first().frequency

        return render_template("/settings.html", username=username, password=password, frequency=frequency, user=user)


@app_bp.route('/settings/email', methods=['GET', 'POST'])
@login_required
def settings_email():
    if request.method == "GET":
        return redirect(url_for("app_bp.settings"))
    else:
        user = User.query.filter_by(id=current_user.id).first()
        if request.form["emailSender"] != "":
            user.replyToEmail = request.form["emailSender"]
        if request.form["emailTitle"] != "":
            user.signature = request.form["emailTitle"]
        db.session.commit()
        send_teacher_email_reports()
        flash("Email successfully sent!")

        return redirect(url_for("app_bp.settings"))


@app_bp.route('/settings/studentEmail', methods=['GET', 'POST'])
@login_required
def settings_student_email():
    if request.method == "GET":
        return redirect(url_for("app_bp.settings"))
    else:
        send_student_email_reports()
        flash("Emails sent for each active student.")

        return redirect(url_for("app_bp.settings"))


@app_bp.route('/settings/emailUpdate', methods=['GET', 'POST'])
@login_required
def settings_email_update():
    if request.method == "GET":
        return redirect(url_for("settings"))
    else:
        user = User.query.filter_by(id=current_user.id).first()
        if request.form["emailSender"] != "":
            user.replyToEmail = request.form["emailSender"]
        if request.form["emailTitle"] != "":
            user.signature = request.form["emailTitle"]
        if request.form.get('isEnabled') == "enabled":
            user.studentEnabled = True
            scheduler.add_job(
                func=send_student_email_reports,
                trigger="interval",
                days=frequency.frequency,
                id="studentEmails",
                name="studentEmails",
                replace_existing=True
            )
            flash("Student emails added to the scheduler.")
        else:
            user.studentEnabled = False
            if scheduler.get_job(id="studentEmails"):
                scheduler.delete_job(id="studentEmails")
            flash("Student emails removed from the scheduler.")


        db.session.commit()
        flash("Email info updated.")

        return redirect(url_for("app_bp.settings"))


@app_bp.route('/settings/database', methods=['GET', 'POST'])
@login_required
def settings_database():
    if request.method == "GET":
        return redirect(url_for("app_bp.settings"))
    else:
        database()
        flash("Database updated for the day.")

        return redirect(url_for("app_bp.settings"))


@app_bp.route('/database', methods=['GET', 'POST'])
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


@app_bp.route('/database/archive', methods=['GET', 'POST'])
@login_required
def view_archived():
    if request.method == "GET":
        students = Student.query.all()
        date = Scrape.query.order_by(Scrape.date.desc()).first().date
        scrapes = Scrape.query.filter_by(date=date).all()
        return render_template("archive-database.html", posts=students, scrapes=scrapes)


@app_bp.route('/database/points', methods=['GET', 'POST'])
@login_required
def points():
    if request.method == "GET":
        # database()
        students = Student.query.all()
        # points = Scrape.query.order_by(Scrape.points).first().points
        date = Scrape.query.order_by(Scrape.date.desc()).first().date
        scrapes = Scrape.query.order_by(Scrape.points.desc()).filter_by(date=date).all()

        return render_template("database.html", posts=students, scrapes=scrapes)


@app_bp.route('/database/change', methods=['GET', 'POST'])
@login_required
def change():
    if request.method == "GET":
        students = Student.query.all()
        date = Scrape.query.order_by(Scrape.date.desc()).first().date
        scrapes = Scrape.query.order_by(Scrape.change.desc()).filter_by(date=date).all()

        return render_template("database.html", posts=students, scrapes=scrapes)


@app_bp.route('/database/<int:period>', methods=['GET', 'POST'])
@login_required
def period(period):
    if request.method == "GET":
        date = Scrape.query.order_by(Scrape.date.desc()).first().date
        scrapes = Scrape.query.order_by(Scrape.change.desc()).filter_by(date=date).all()
        return render_template("period-database.html", scrapes=scrapes, period=period)


@app_bp.route('/database/view/<string:theClass>', methods=['GET', 'POST'])
@login_required
def theClass(theClass):
    if request.method == "GET":
        date = Scrape.query.order_by(Scrape.date.desc()).first().date
        scrapes = Scrape.query.order_by(Scrape.change.desc()).filter_by(date=date).all()
        return render_template("class-database.html", scrapes=scrapes, theClass=theClass)


@app_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out.")
    return redirect(url_for("app_bp.login"))


@app_bp.route('/student/<int:scrape_student_id>', methods=['GET', 'POST'])
@login_required
def display_student(scrape_student_id):
    fetched_student = Student.query.get(scrape_student_id)
    scrapes = Scrape.query.filter_by(student_id=scrape_student_id).order_by(Scrape.date.desc()).all()

    fig, ax = plt.subplots(figsize = (2.5,2.5))
    ax.set_xlabel('Scrape')
    ax.set_ylabel('Points')
    ax.set_title('Scrape Table')
    points = []
    for i in reversed(range(len(scrapes))):
        points.append(scrapes[i].points)
    ax.plot(points)
    plt.tight_layout()
    plt.ylim([scrapes[-1].points-20, scrapes[-1].points+20])

    html_fig = mpld3.fig_to_html(fig)

    return render_template("/student.html", student=fetched_student, scrapes=scrapes, graph=html_fig)


@app_bp.route('/student/<int:student_id>/edit', methods=['GET', 'POST'])
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
        fetched_student.memo = request.form["memo"]
        if request.form.get('isArchived') == "isArchived":
            fetched_student.isArchived = True
        else:
            fetched_student.isArchived = False
        flash("Student info updated.")
        db.session.commit()

        scrapes = Scrape.query.filter_by(student_id=student_id).order_by(Scrape.date.desc()).all()
        fig, ax = plt.subplots(figsize=(2.5, 2.5))
        ax.set_xlabel('Scrape')
        ax.set_ylabel('Points')
        ax.set_title('Scrape Table')
        points = []
        for i in reversed(range(len(scrapes))):
            points.append(scrapes[i].points)
        ax.plot(points)
        plt.tight_layout()
        plt.ylim([scrapes[-1].points - 20, scrapes[-1].points + 20])

        html_fig = mpld3.fig_to_html(fig)
        return render_template("/student.html", student=fetched_student, scrapes=scrapes, graph=html_fig)


@app_bp.route('/json', methods=['GET', 'POST'])
@login_required
def json_creator():
    date = Scrape.query.order_by(Scrape.date.desc()).first().date
    students = Student.query.all()
    theStudents = []

    for student in students:
        scrape = Scrape.query.filter_by(student_id=student.id).filter_by(date=date).first()
        student = {
            "rank": scrape.ranking,
            "points": scrape.points,
            "change": scrape.change,
            "memo": student.memo
        }
        theStudents.append(student)
    # print(theStudents)
    studentDict = dict(date=str(date), students=theStudents)
    # theJson = json.dumps(studentDict)
    return studentDict