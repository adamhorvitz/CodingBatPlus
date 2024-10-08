from datetime import date
from bs4 import BeautifulSoup
from requests import Session
from flask import flash
from .models import Frequency, User, Scrape, Student
from .functions import change_in_points, send_teacher_email_reports
from . import db, scheduler

# Check if the frequency already exists; if not, create it
try:
    frequency = Frequency.query.first()
    if frequency is None:
        frequency = Frequency()
        db.session.add(frequency)
        db.session.commit()
except:
    db.create_all()
    db.session.close()
    frequency = Frequency()
    db.session.add(frequency)
    db.session.commit()


# Function that scrapes CodingBat and updates the database with the points for each student
@scheduler.task('interval', id='database', days=frequency.frequency, misfire_grace_time=900)
def database():
    # Get the user's info
    user = User.query.order_by(User.id.desc()).first()
    username = user.codingbat_email
    password = user.codingbat_password
    # Access the CodingBat website using the Session function and BeautifulSoup
    try:
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
        # Look for all tables and then the tr parameter on CodingBat
        soup = BeautifulSoup(home_page.content, 'html.parser')
        tbody = soup.find_all('table')[2]
        emailList = []
        tr = tbody.find_all('tr')
        print(tr)
    except:
        flash("Incorrect CodingBat username and/or password. Update the values and try again.")
        return

    last_scrape_entry = Scrape.query.order_by(Scrape.date.desc()).first()
    # Short-circuit to check if the last scrape entry doesn't exist or today has already been scraped
    if last_scrape_entry is None or (last_scrape_entry is not None and last_scrape_entry.date != date.today()):
        print("RUNNING DATABASE")
        # Go through a loop of each student, start at 2 since the info before does not contain scrape info
        for x in range(2, len(tr)):
            row_data = tr[x].findAll("td")
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

            # 5. Commit and add to database

            db.session.add(scrape)

            emailList.append([email, memo, points])

        db.session.commit()
        # Calculate the ranking and change for each student
        Scrape.calc_ranking()
        change_in_points()
        # Send the reports to the teacher for the current scrape
        send_teacher_email_reports()