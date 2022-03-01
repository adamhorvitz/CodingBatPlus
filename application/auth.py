from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_required, logout_user, current_user, login_user
from .routes import app_bp
from . import db, login_manager
from .models import User
from .scheduler import database


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


@login_manager.unauthorized_handler
def unauthorized():
    flash("You must be logged in to view that page.")
    return redirect(url_for("app_bp.login"))


@app_bp.route('/', methods=['GET', 'POST'])
def login():  # put application's code here
    if request.method == 'GET':
        if current_user.is_authenticated:
            return redirect(url_for('app_bp.view_posts'))
        return render_template("login.html")
    else:
        email = request.form["email"]
        user = User.query.filter_by(email=email).first()
        password = request.form["password"]
        if user and user.check_password(password=password):  # If the user exists and the password is correct
            login_user(user)
            flash("Login successful.")
            return redirect(url_for("app_bp.view_posts"))
        flash("Login unsuccessful. Please try again or create a new account.")
        return redirect(url_for("app_bp.login"))


@app_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == "GET":
        if current_user.is_authenticated:
            return redirect(url_for('app_bp.view_posts'))

    else:
        # Logic for creating a new user, then logging them in
        email = request.form["email"]
        secretKey = request.form["secretKey"]
        if secretKey != "NBPS2022":
            flash("Secret key incorrect.")
            return render_template("signup.html")
        existing_user = User.query.filter_by(email=email).first()
        if existing_user is None:
            user = User(email=email)
            user.set_password(request.form["password"])
            user.replyToEmail = email
            db.session.add(user)
            db.session.commit()
            login_user(user)
            database()
            flash("User created!")
            return redirect(url_for("app_bp. view_posts"))
        flash("A user with that email already exists.")
    return render_template("signup.html")