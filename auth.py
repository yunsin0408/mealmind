from flask import Blueprint, render_template, redirect, url_for, request, flash
from models import db, User
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from email_utils import send_confirmation_email, confirm_token


auth = Blueprint('auth', __name__)

# Register route
@auth.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        if User.query.filter_by(username=username).first():
            flash("Username already exists")
            return redirect(url_for("auth.register"))

        new_user = User(username=username, email=email, password=password)

        db.session.add(new_user)
        db.session.commit()

        send_confirmation_email(new_user.email)
        flash("A confirmation email has been sent. Please check your inbox.", "info")
        return redirect(url_for("auth.login"))
    return render_template("register.html")

@auth.route("/confirm/<token>")
def confirm_email(token):
    email = confirm_token(token)
    if not email:
        flash("The confirmation link is invalid or has expired.", "danger")
        return redirect(url_for("auth.login"))

    user = User.query.filter_by(email=email).first_or_404()
    if user.is_confirmed:
        flash("Account already confirmed. Please login.", "success")
    else:
        user.is_confirmed = True
        db.session.commit()
        flash("You have confirmed your account! Have fun cooking with MealMind!", "success")
    return redirect(url_for("auth.login"))

# Login route
@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("index"))
        else:
            flash("Invalid username or password")
            return redirect(url_for("auth.login"))

    return render_template("login.html")


# Logout route
@auth.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))
