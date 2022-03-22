from flask_login import LoginManager, UserMixin, login_required, logout_user, current_user, login_user
from flask_mail import Mail, Message
from .models import Frequency, User, Scrape, Student
from . import db, mail


# Send report to each active student with their individual stats and ranking
def send_student_email_reports():
    students = Student.query.filter_by(isArchived=False).all()
    user = User.query.filter_by(id=current_user.id).first()
    date = Scrape.query.order_by(Scrape.date.desc()).first().date
    # Go through each active student, get their points, change, and ranking and send the message
    for student in students:
        scrape = Scrape.query.filter_by(student_id=student.id).filter_by(date=date).first()
        msg = Message("Your Weekly CodingBat Progress", sender=user.replyToEmail, recipients=[student.email])
        body = "Hey " + student.memo + ", here's how you're doing this week on CodingBat!\n\n"
        body += "You have " + str(scrape.points) + " points.\n"
        body += "Since last week, you've changed by " + str(scrape.change) + " points.\n"
        body += "Your ranking is #" + str(scrape.ranking) + ".\n"
        body += "Improve your stats for a chance to be featured in next week's teacher report!\n\n"
        body += user.signature
        print(body)
        msg.body = body
        mail.send(msg)

    return "Messages sent!"


# Send a report to the teacher with the top 5 students as of each scrape
def send_teacher_email_reports():
    user = User.query.filter_by(id=current_user.id).first()

    date = Scrape.query.order_by(Scrape.date.desc()).first().date
    scrapes = Scrape.query.order_by(Scrape.points.desc()).filter_by(date=date).limit(5).all()
    msg = Message("CodingBat+ Scrape Info", sender='codingbatplus@gmail.com', recipients=[user.replyToEmail])
    body = "Hey, here's the top 5 scrapes as of " + str(date.today()) + "!\n\n"
    # Go through the top 5 scrapes and concatenate the body with their ranking and points
    for scrape in scrapes:
        body += str(scrape.student.memo) + " is #" + str(scrape.ranking) + " with " + str(
            scrape.points) + " points\n"

    scrapes = Scrape.query.order_by(Scrape.change.desc()).filter_by(date=date).limit(5).all()
    # If none of these are improved then don't include this part at all
    improved = ""
    counter = 0
    for scrape in scrapes:
        if scrape.change > 0:
            improved += str(scrape.student.memo) + " has changed by " + str(scrape.change) + " points\n"
            counter += 1
    if counter != 0:
        body += "\nAnd here are the most improved!\n\n"
        body += improved

    body += "\n"
    body += user.signature
    msg.body = body
    mail.send(msg)
    return "Message sent!"


# Calculate the change in points from the last database scrape
def change_in_points():
    students = Student.query.all()

    # Go through each student and compare their current scrape to the last one
    for student in students:
        studentPoints = []
        scrapes = Scrape.query.order_by(Scrape.date).filter_by(student_id=student.id).all()
        # Order the scrapes for each student from most recent date to last
        for scrape in scrapes:
            studentPoints.append(scrape.points)
            # Calculate the difference from current scrape and the one before
            if len(studentPoints) > 1:
                print(studentPoints)
                change = studentPoints[-1] - studentPoints[-2]
                scrape.change = change
                # db.session.add(scrape)
            else:
                scrape.change = 0

    print("Running change")
    db.session.commit()


# Calculate the students' rankings based on their current points
def ranking():
    date = Scrape.query.order_by(Scrape.date.desc()).first().date
    scrapes = Scrape.query.order_by(Scrape.points.desc()).filter_by(date=date).all()
    ranking = 1
    # For every scrape, add their ranking to the database
    for scrape in scrapes:
        scrape.ranking = ranking
        db.session.add(scrape)
        # print(ranking)
        ranking += 1

    db.session.commit()


# Calculate rankings based on each student's class
def rank_class():
    date = Scrape.query.order_by(Scrape.date.desc()).first().date
    scrapes = Scrape.query.order_by(Scrape.points.desc()).filter_by(date=date).all()
    ranking = 1
    # For every scrape, add their ranking to the database
    for scrape in scrapes:
        scrape.ranking = ranking
        db.session.add(scrape)
        # print(ranking)
        ranking += 1

    db.session.commit()


# Calculate rankings based on each student's period
def rank_period():

    date = Scrape.query.order_by(Scrape.date.desc()).first().date
    scrapes = Scrape.query.order_by(Scrape.points.desc()).filter_by(date=date).all()
    ranking = 1
    # For every scrape, add their ranking to the database
    for scrape in scrapes:
        scrape.ranking = ranking
        db.session.add(scrape)
        # print(ranking)
        ranking += 1

    db.session.commit()


# For debugging purposes: go through the current date and delete all scrapes for that day
def date_deleter():
    date = Scrape.query.order_by(Scrape.date.desc()).first().date
    scrapes = Scrape.query.filter_by(date=date).all()

    for scrape in scrapes:
        db.session.delete(scrape)

    db.session.commit()
