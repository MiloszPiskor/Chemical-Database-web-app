from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required, login_manager
from flask_ckeditor import CKEditor
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect
from sqlalchemy.orm import DeclarativeBase
from werkzeug.security import generate_password_hash, check_password_hash
from flask_bootstrap import Bootstrap5
from datetime import date
from models import User, Product, Company, LineItem, ProductCompany, db
from forms import RegisterForm, LoginForm, EntryForm, CompanyForm, ProductForm
from dotenv import load_dotenv
import os

def user_check(email):
    """A function making a check during registration for User in Database,
     if they exist redirects them to the login page."""

    check_for_user = User.query.filter_by(email=email).first()
    if check_for_user:
        flash("You are already registered in our database. Please log in.")
        email = email
        return redirect(url_for("login", email=email))

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

def admin_only(function):
    @wraps(function)
    def wrapper_function(*args, **kwargs):
        if current_user.is_authenticated and current_user.id == 1:
            return function(*args, **kwargs)
        else:
            return jsonify(error = "Unauthorized access"), 401
    return wrapper_function

# Loading the environment variables
load_dotenv()

# Initialising the app
app = Flask(__name__)
ckeditor = CKEditor(app)
bootstrap = Bootstrap5(app)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
# Login Manager setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message = u"Please login first."

# CREATE DATABASE
class Base(DeclarativeBase):
    pass
# Load database URI from environment variables
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI', 'sqlite:///mydatabase.db')
# Initialize the db with the app
db.init_app(app)

with app.app_context():
    if not inspect(db.engine).has_table("users"):
        app.logger.error("The 'user' table does not exist.")
    else:
        app.logger.info("User table exists and is ready for queries.")

with app.app_context():
    app.logger.info(f"Registered routes: {[rule.rule for rule in app.url_map.iter_rules()]}")

with app.app_context():
    inspector = inspect(db.engine)
    if not inspector.has_table("users"):
        print("No database found, proceeding to instantiate the Model.")
        db.create_all()
    else:
        print("The database exists, no need to initialize the Model.")

@login_manager.user_loader
def load_user(user_id):
    return User.query.get_or_404(user_id)

@app.route("/register", methods=["POST", "GET"])
def register():

    form = RegisterForm()
    if form.validate_on_submit():
        app.logger.info("Register Form successfully submitted.")
        # Check if User in database:
        user_check(email=form.email.data)
        # Creating a new User object:
        new_user = User(name=form.name.data, email=form.email.data)
        # Hashed password management for user:
        new_user.set_password(password=form.password.data)

        try:
            db.session.add(new_user)
            db.session.commit()
            app.logger.info(f"User: {new_user.name} successfully added to the database.")
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"User: {new_user.name} not added to the database due to the error: {e}.")
            flash("An error occurred during the registration, please try again!")

        login_user(new_user)
        flash("You've been successfully registered!", category="success")
        return redirect(url_for("home"))


    return render_template("register.html", form = form)

@app.route("/login", methods=["POST", "GET"])
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
            return redirect(url_for('register'))
        # Checking for a password match
        if not existing_user.check_password(password=form.password.data):
            flash("Incorrect password.")
            return redirect(url_for('login'))
        #Logging User in
        login_user(existing_user)
        flash("Successfully logged in!", category="success")
        # Default to 'homepage' path
        next_url = url_for("homepage")
        # Override next_url if it's valid
        captured_url = request.args.get('next')
        if captured_url and _url_has_allowed_host_and_scheme(next_url, request.host):
            next_url = current_user
            app.logger.info(f"The captured url for unauthorized entry has been fetched. Redirecting to: {next_url}...")

        return redirect(next_url)

    return render_template("login.html", form= form)

@app.route('/logout')
def logout():

    logout_user()
    app.logger.info("User successfully logged out.")
    flash("You've been successfully logged out.", category="success")
    return redirect(url_for('login'))

@app.route("/")
def home():

    return render_template("index.html")

@app.route("/new-entry", methods=["GET", "POST"])
def add_entry():

    form = EntryForm()
    # Filling the Select Field for products registered by the current user
    # user_products = current_user.products # Product.query.order_by(Product.name).all()  SETUP FOR PRODUCTION AFTER ADDING LOGGING
    user_products = Product.query.order_by(Product.name).all()
    form.product_name.choices = [(p.id, p.name) for p in user_products]

    # Filling the Select Field for companies registered by the current user
    # user_companies = current_user.companies SETUP FOR PRODUCTION AFTER ADDING LOGGING
    user_companies = Company.query.order_by(Company.name).all()
    form.company_name.choices = [(p.id, p.name) for p in user_companies]

    return render_template('add_entry.html', form=form)

@app.route("/new-company", methods=["GET", "POST"])
def add_company():

    form = CompanyForm()

    return render_template('add_company.html', form=form)

@app.route("/new-product", methods=["GET", "POST"])
def add_product():

    pass



if __name__ == "__main__":
    app.run(debug=True, port=5002)