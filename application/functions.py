from flask_login import LoginManager, UserMixin, login_required, logout_user, current_user, login_user
from flask_mail import Mail, Message
from .models import Frequency, User, Scrape, Student
from . import db, mail


def send_student_email_reports():
    students = Student.query.filter_by(isArchived=False).all()
    user = User.query.filter_by(id=current_user.id).first()
    date = Scrape.query.order_by(Scrape.date.desc()).first().date
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


def send_teacher_email_reports():
    user = User.query.filter_by(id=current_user.id).first()

    date = Scrape.query.order_by(Scrape.date.desc()).first().date
    scrapes = Scrape.query.order_by(Scrape.points.desc()).filter_by(date=date).limit(5).all()
    msg = Message("CodingBat+ Scrape Info", sender='codingbatplus@gmail.com', recipients=[user.replyToEmail])
    body = "Hey, here's the top 5 scrapes as of " + str(date.today()) + "!\n\n"
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

    body+= "\n"
    body += user.signature
    # print(body)
    # jsonMsg = json.dumps(body)
    # # print(jsonMsg)
    msg.body = body
    mail.send(msg)
    return "Message sent!"




def change_in_points():
    students = Student.query.all()

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


def rank_class():
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


def rank_period():
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




