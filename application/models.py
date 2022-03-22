from datetime import date
from flask_login import LoginManager, UserMixin, login_required, logout_user, current_user, login_user
from werkzeug.security import generate_password_hash, check_password_hash
from . import db

# Model for Student contained in each scrape
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


# Model for each Scrape, updated every time the database runs
class Scrape(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    points = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, default=date.today())
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    change = db.Column(db.Integer, nullable=True)

    def __repr__(self):
        return '<Scrape %r>' % self.id


# Model for Frequency- how often the database runs
class Frequency(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    frequency = db.Column(db.Integer, default=1)

    def __repr__(self):
        return str(self.frequency)


# Model for User who can sign up/log in
class User(UserMixin, db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True
    )
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

    replyToEmail = db.Column(db.String(500), unique=False, nullable=True)
    studentEnabled = db.Column(db.Boolean, unique=False, nullable=True, default=False)
    signature = db.Column(db.String(500), unique=False, nullable=True, default="CodingBat+ Scrape Data")

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