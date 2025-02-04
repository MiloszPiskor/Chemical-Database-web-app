from functools import wraps
import logging
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required, login_manager
from flask_ckeditor import CKEditor
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect
from sqlalchemy.orm import DeclarativeBase
from flask_bootstrap import Bootstrap5
from datetime import date
from models import User, Product, Company, LineItem, ProductCompany, db
from forms import RegisterForm, LoginForm, EntryForm, CompanyForm, ProductForm
from companies import companies_bp
from products import products_bp
from users import users_bp
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

def product_check(name):
    """A function that checks if a product entered in the Product Form
    already exists in a database, if it does it redirects the User to the
    specific Product page"""
    check_for_product = Product.query.filter_by(name=name).first()
    if check_for_product:
        flash("This product already exists in the database.")
        return redirect(url_for("products"))

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
# Registering the blueprints
app.register_blueprint(companies_bp)
app.register_blueprint(products_bp)
app.register_blueprint(users_bp)
# Logging setup
if not app.debug:
    handler = logging.FileHandler("app.log")
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)

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
    return User.query.filter_by(id=user_id).first()

@app.route("/")
def home():

    return render_template("index.html")

@app.route("/new-entry", methods=["GET", "POST"])
@login_required
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

# @app.route("/products")
# @login_required
# def products():
#     return render_template('products.html')
#
# @app.route("/edit-product")
# @login_required
# def edit_product():
#
#     id = int(request.args.get('product_id'))
#     product = Product.query.filter_by(id = id).first()
#     form = ProductForm(
#         name = product.name,
#         customs_code = product.customs_code,
#         img_url = product.img_url
#     )
#     if form.validate_on_submit():
#         try:
#             for key, value in form.data.items():
#                 setattr(product, key, value)
#             db.session.commit()
#             flash(f"Successfully implemented changes to the: {product.name}")
#             app.logger.info(f"Changes implemented for product: {product.id}.")
#             return redirect(url_for('products'))
#         except Exception as e:
#             db.session.rollback()
#             app.logger.error(f"Error {e} occurred while editing Product", exc_info=True)
#             flash(f"An error occurred while implementing changes for: {product.name}. Please try again", "danger")
#             return redirect(url_for('products'))
#
#
#
#
#     return render_template('product.html', form = form)
#
# @app.route("/delete-product")
# @login_required
# def delete_product():
#
#     id = request.args.get('product_id')
#     product = Product.query.filter_by(id=id).first()
#
#
# @app.route("/companies")
# @login_required
# def companies():
#     return render_template('companies.html')
#
# @app.route("/new-company", methods=["GET", "POST"])
# @login_required
# def add_company():
#
#     form = CompanyForm()
#
#     return render_template('add_company.html', form=form)
#
# @app.route("/new-product", methods=["GET", "POST"])
# @login_required
# def add_product():
#
#     form = ProductForm()
#     if form.validate_on_submit():
#         product_check(name=form.name.data)
#         new_product = Product(
#             name = form.name.data,
#             customs_code = form.customs_code.data,
#             img_url = form.img_url.data,
#             stock= 0,
#             user = current_user
#         )
#         try:
#             db.session.add(new_product)
#             db.session.commit()
#             app.logger.info(f"New user {new_product.name} added to the database.")
#             flash(f"Success! Added a new product: {new_product.name} to the database.")
#             return redirect(url_for('products'))
#         except Exception as e:
#             db.session.rollback()
#             app.logger.error(f"Error {e} occurred while adding new Product.", exc_info=True)
#             flash(f"An error occurred while adding: {new_product.name} to the database. Please try again", "danger")
#             return redirect(url_for('add_product'))
#
#
#
#
#     return render_template('add_product.html', form=form)

# Two routes handling the AJAX Forms update
@app.route("/add_product_ajax", methods=["POST"])
def add_product_ajax():
    data = request.get_json()
    new_product = Product(name=data["name"])
    db.session.add(new_product)
    db.session.commit()
    return jsonify(success=True, product_id=new_product.id)

@app.route("/add_company_ajax", methods=["POST"])
def add_company_ajax():
    data = request.get_json()
    new_company = Company(name=data["name"])
    db.session.add(new_company)
    db.session.commit()
    return jsonify(success=True, company_id=new_company.id)

if __name__ == "__main__":
    app.run(debug=True, port=5002)