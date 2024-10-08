from datetime import date

import matplotlib.pyplot as plt
import mpld3
from flask import Blueprint
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, logout_user, current_user

from . import db
from .functions import send_student_email_reports, send_teacher_email_reports
from .models import User, Frequency, Student, Scrape
from .scheduler import database, scheduler, frequency

# Blueprint Configuration
app_bp = Blueprint(
    'app_bp', __name__,
    template_folder='templates',
    static_folder='static'
)


# Route for Settings page
@app_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == "GET":
        print(date.today())
        frequency = Frequency.query.first().frequency
        user = User.query.filter_by(id=current_user.id).first()
        username = user.codingbat_email
        password = user.codingbat_password
        return render_template("/settings.html", username=username, password=password, frequency=frequency, user=user)
    else:
        # Get the changed frequency and update it to either month, week, or daily
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

        # Update the scheduler with the NEW frequency
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


# Route for the Settings page changing the login information
@app_bp.route('/settings/login', methods=['GET', 'POST'])
@login_required
def settings_login():
    if request.method == "GET":
        return redirect(url_for("app_bp.settings"))
    else:
        #Get the user inputted username and password and update their email with it
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


# Route for the Settings page containing the teacher email information
@app_bp.route('/settings/email', methods=['GET', 'POST'])
@login_required
def settings_email():
    if request.method == "GET":
        return redirect(url_for("app_bp.settings"))
    else:
        # Get the user's email information and manually send out teacher reports
        user = User.query.filter_by(id=current_user.id).first()
        if request.form["emailSender"] != "":
            user.replyToEmail = request.form["emailSender"]
        if request.form["emailTitle"] != "":
            user.signature = request.form["emailTitle"]
        db.session.commit()
        send_teacher_email_reports()
        flash("Email successfully sent!")

        return redirect(url_for("app_bp.settings"))


# Route for the Settings page containing the student email information
@app_bp.route('/settings/studentEmail', methods=['GET', 'POST'])
@login_required
def settings_student_email():
    if request.method == "GET":
        return redirect(url_for("app_bp.settings"))
    else:
        # Send student reports for each active student
        send_student_email_reports()
        flash("Emails sent for each active student.")

        return redirect(url_for("app_bp.settings"))


# Route for the Settings page changing the email information
@app_bp.route('/settings/emailUpdate', methods=['GET', 'POST'])
@login_required
def settings_email_update():
    if request.method == "GET":
        return redirect(url_for("settings"))
    else:
        # Get the current user, change the email sender and title to the form inputted
        user = User.query.filter_by(id=current_user.id).first()
        if request.form["emailSender"] != "":
            user.replyToEmail = request.form["emailSender"]
        if request.form["emailTitle"] != "":
            user.signature = request.form["emailTitle"]
        if request.form.get('isEnabled') == "enabled":
            user.studentEnabled = True
            # Update the scheduler with the student reports
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


# Route for the Settings page containing the database  information
@app_bp.route('/settings/database', methods=['GET', 'POST'])
@login_required
def settings_database():
    if request.method == "GET":
        return redirect(url_for("app_bp.settings"))
    else:
        # Run the database for the day if the user manually clicks it
        database()
        flash("Database updated for the day.")
        return redirect(url_for("app_bp.settings"))


# Route for the Database page containing the current day's scrape information
@app_bp.route('/database', methods=['GET', 'POST'])
@login_required
def view_posts():
    if request.method == "GET":
        # Check if students exist; if they don't, run the database for the first time
        try:
            students = Student.query.all()
            date = Scrape.query.order_by(Scrape.date.desc()).first().date
        except:
            database()
            print('Running exception')
            students = Student.query.all()
            date = Scrape.query.order_by(Scrape.date.desc()).first().date
        scrapes = Scrape.query.filter_by(date=date).all()
        return render_template("database.html", posts=students, scrapes=scrapes)

# Route for the Archived Database page containing the current day's archived student information
@app_bp.route('/database/archive', methods=['GET', 'POST'])
@login_required
def view_archived():
    if request.method == "GET":
        # Get all the students
        students = Student.query.all()
        date = Scrape.query.order_by(Scrape.date.desc()).first().date
        scrapes = Scrape.query.filter_by(date=date).all()
        return render_template("archive-database.html", posts=students, scrapes=scrapes)


# Route for the Database page containing the current day's scrape information sorted by points
@app_bp.route('/database/points', methods=['GET', 'POST'])
@login_required
def points():
    if request.method == "GET":
        students = Student.query.all()
        date = Scrape.query.order_by(Scrape.date.desc()).first().date
        scrapes = Scrape.query.order_by(Scrape.points.desc()).filter_by(date=date).all()

        return render_template("database.html", posts=students, scrapes=scrapes)


# Route for the Database page containing the current day's scrape information sorted by change
@app_bp.route('/database/change', methods=['GET', 'POST'])
@login_required
def change():
    if request.method == "GET":
        students = Student.query.all()
        date = Scrape.query.order_by(Scrape.date.desc()).first().date
        scrapes = Scrape.query.order_by(Scrape.change.desc()).filter_by(date=date).all()

        return render_template("database.html", posts=students, scrapes=scrapes)

# Route for the Database page containing the current day's scrape information filtered by period
@app_bp.route('/database/<int:period>', methods=['GET', 'POST'])
@login_required
def period(period):
    if request.method == "GET":
        date = Scrape.query.order_by(Scrape.date.desc()).first().date
        scrapes = Scrape.query.order_by(Scrape.change.desc()).filter_by(date=date).all()
        return render_template("period-database.html", scrapes=scrapes, period=period)


# Route for the Database page containing the current day's scrape information filtered by class
@app_bp.route('/database/view/<string:theClass>', methods=['GET', 'POST'])
@login_required
def theClass(theClass):
    if request.method == "GET":
        date = Scrape.query.order_by(Scrape.date.desc()).first().date
        scrapes = Scrape.query.order_by(Scrape.change.desc()).filter_by(date=date).all()
        return render_template("class-database.html", scrapes=scrapes, theClass=theClass)


# Route for the Leaderboards page containing lists of each period and class
@app_bp.route('/leaderboards', methods=['GET', 'POST'])
@login_required
def leaderboards():
    students = Student.query.all()
    date = Scrape.query.order_by(Scrape.date.desc()).first().date
    scrapes = Scrape.query.filter_by(date=date).all()
    periodsList = Student.query.with_entities(Student.period).distinct()
    periods = [row.period for row in periodsList.all()]
    classList = Student.query.with_entities(Student.theClass).distinct()
    classes = [row.theClass for row in classList.all()]
    return render_template("leaderboards.html", students=students, scrapes=scrapes, periods=periods, classes=classes)


# Route for the Leaderboard page containing the top 10 leaderboard filtered by period
@app_bp.route('/leaderboards/<int:period>', methods=['GET', 'POST'])
@login_required
def leaderboards_period(period):
    date = Scrape.query.order_by(Scrape.date.desc()).first().date
    scrapes = Scrape.query.order_by(Scrape.points.desc()).filter_by(date=date).limit(10).all()
    return render_template("leaderboards-period.html", scrapes=scrapes, period=period)


# Route for the Leaderboard page containing the top 10 leaderboard filtered by class
@app_bp.route('/leaderboards/class/<string:theClass>', methods=['GET', 'POST'])
@login_required
def leaderboards_class(theClass):
    date = Scrape.query.order_by(Scrape.date.desc()).first().date
    scrapes = Scrape.query.order_by(Scrape.points.desc()).filter_by(date=date).limit(10).all()
    return render_template("leaderboards-class.html", scrapes=scrapes, theClass=theClass)


# Log out the current user
@app_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out.")
    return redirect(url_for("app_bp.login"))

# Route for the Student page containing all of the scrapes per student and their information
@app_bp.route('/student/<int:scrape_student_id>', methods=['GET', 'POST'])
@login_required
def display_student(scrape_student_id):
    fetched_student = Student.query.get(scrape_student_id)
    scrapes = Scrape.query.filter_by(student_id=scrape_student_id).order_by(Scrape.date.desc()).all()

    # Using subplots, create a plot with the students' scrape and points
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

# Route for the student page with an option to edit their information
@app_bp.route('/student/<int:student_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_student(student_id):
    if request.method == "GET":
        fetched_student = Student.query.get(student_id)
        scrapes = Scrape.query.filter_by(student_id=student_id).order_by(Scrape.date.desc()).all()
        return render_template("/student-edit.html", student=fetched_student, scrapes=scrapes)
    else:
        # Get all of the changed info and update the students' parameters with the fetched forms
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
        # Using subplots, create a plot with the students' scrape and points
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


# Route for JSON object of each student's rank, points, change, and memo
@app_bp.route('/json', methods=['GET', 'POST'])
@login_required
def json_creator():
    date = Scrape.query.first().date # Access database and query Scrapes
    students = Student.query.filter_by(isArchived=False).all() # Filter Students by not archived
    theStudents = []
    # Go through each student and create a dictionary of their info
    for student in students:
        scrape = Scrape.query.filter_by(student_id=student.id).filter_by(date=date).first()
        student = {
            "rank": scrape.ranking,
            "points": scrape.points,
            "change": scrape.change,
            "memo": student.memo
        }
        theStudents.append(student) # Add each student to the dictionary
    # Create a dictionary of dictionaries for the student and return it
    theStudents = sorted(theStudents, key=lambda x: (x['points']), reverse=True)
    studentDict = dict(date=str(date), students=theStudents)
    return studentDict # Return as JSON object
