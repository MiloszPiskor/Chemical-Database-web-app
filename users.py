from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, Blueprint, current_app
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required, login_manager
from flask_ckeditor import CKEditor
from models import User, Product, Company, LineItem, ProductCompany, db
from forms import RegisterForm, LoginForm, EntryForm, CompanyForm, ProductForm
import os

def user_check(email):
    """A function making a check during registration for User in Database,
     if they exist redirects them to the login page."""

    check_for_user = User.query.filter_by(email=email).first()
    if check_for_user:
        flash("You are already registered in our database. Please log in.")
        email = email
        return redirect(url_for("users.login", email=email))


def _url_has_allowed_host_and_scheme(url, allowed_hosts, require_https=False):
    if url is not None:
        url = url.strip()

    if not url:
        return False

    if allowed_hosts is None:
        allowed_hosts = set()
    elif isinstance(allowed_hosts, str):
        allowed_hosts = {allowed_hosts}

    # Normalize the path by replacing backslashes with forward slashes
    normalized_url = url.replace('\\', '/')

    return True

users_bp = Blueprint("users", __name__)

@users_bp.route("/register", methods=["POST", "GET"])
def register():

    form = RegisterForm()
    if form.validate_on_submit():
        current_app.logger.info("Register Form successfully submitted.")
        # Check if User in database:
        user_check(email=form.email.data)
        # Creating a new User object:
        new_user = User(name=form.name.data, email=form.email.data)
        # Hashed password management for user:
        new_user.set_password(password=form.password.data)

        try:
            db.session.add(new_user)
            db.session.commit()
            current_app.logger.info(f"User: {new_user.name} successfully added to the database.")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"User: {new_user.name} not added to the database due to the error: {e}.")
            flash("An error occurred during the registration, please try again!")

        login_user(new_user)
        flash("You've been successfully registered!", category="success")
        return redirect(url_for("home"))


    return render_template("register.html", form = form)

@users_bp.route("/login", methods=["POST", "GET"])
def login():

    form = LoginForm()
    # Email field autofill for the redirected User from registration if they are already registered
    if request.args.get("email"):
        form = LoginForm(
            email = request.args.get("email")
        )

    if form.validate_on_submit():
        # Check if User exists in DB, if not redirect them to registration
        existing_user = db.session.execute(db.select(User).where(User.email == form.email.data)).scalar_one_or_none()
        if not existing_user:
            flash("You need to be registered to log in.")
            return redirect(url_for('users.register'))
        # Checking for a password match
        if not existing_user.check_password(password=form.password.data):
            flash("Incorrect password.")
            return redirect(url_for('users.login'))
        #Logging User in
        login_user(existing_user)
        flash("Successfully logged in!", category="success")
        # Default to 'homepage' path
        next_url = url_for("home")
        # Override next_url if it's valid
        captured_url = request.args.get('next')
        current_app.logger.info(f"Current captured url is:{captured_url}")
        if captured_url and _url_has_allowed_host_and_scheme(next_url, request.host):
            next_url = captured_url
            current_app.logger.info(f"The captured url for unauthorized entry has been fetched. Redirecting to: {next_url}...")

        return redirect(next_url)

    return render_template("login.html", form= form)

@users_bp.route('/logout')
@login_required
def logout():

    logout_user()
    current_app.logger.info("User successfully logged out.")
    flash("You've been successfully logged out.", category="success")
    return redirect(url_for('users.login'))