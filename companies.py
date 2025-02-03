from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, Blueprint
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

companies_bp = Blueprint("companies", __name__)

@companies_bp.route("/companies")
@login_required
def companies():
    return render_template('companies.html')

@companies_bp.route("/new-company", methods=["GET", "POST"])
@login_required
def add_company():

    form = CompanyForm()

    return render_template('add_company.html', form=form)