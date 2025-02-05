from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, Blueprint, current_app
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required, login_manager
from flask_ckeditor import CKEditor
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect
from sqlalchemy.orm import DeclarativeBase
from werkzeug.exceptions import NotFound
from werkzeug.security import generate_password_hash, check_password_hash
from flask_bootstrap import Bootstrap5
from datetime import date
from models import User, Product, Company, LineItem, ProductCompany, db
from forms import RegisterForm, LoginForm, EntryForm, CompanyForm, ProductForm
from dotenv import load_dotenv
import os
import logging


companies_bp = Blueprint("companies", __name__)

def company_check(name):
    """A function that checks if a company entered in the Company Form
    already exists in a database."""
    check_for_company = Company.query.filter_by(name=name).first()
    return check_for_company

def assign_company_to_user(user_id, company_id):
    try:
        company = Company.query.get(company_id)
        user = User.query.get(user_id)

        if not company:
            return jsonify(error="Company not found"), 404
        if not user:
            return jsonify(error="User not found"), 404

        company.user = user  # Assign the user using SQLAlchemy ORM
        db.session.commit()

        return jsonify(success=f"Company {company_id} assigned to user {user_id}"), 200

    except Exception as e:
        db.session.rollback()
        return jsonify(error=str(e)), 500

# with app.app_context():
#     if not current_app.debug:  # Ensure logging in production mode
#         current_app.logger.setLevel(logging.INFO)

@companies_bp.route("/companies/<int:company_id>")
def get_company(company_id):

    try:
        company = db.get_or_404(Company, company_id)
        current_app.logger.info(f"Company retrieved: {company.id} by func: {get_company.__name__}")
        return jsonify(company.to_dict()), 200

    except NotFound:
        current_app.logger.warning(f"Company with ID: {company_id} not found.")
        return jsonify(error=f"Company of ID: {company_id} not found."), 404

    except Exception as e:
        current_app.logger.error(f"Unexpected error in {get_company.__name__}: {str(e)}")
        return jsonify(error="Internal server error"), 500

@companies_bp.route("/companies")
def get_companies():

    print(f"Companies of the user:{User.query.get(1).companies}")
    try:
        companies = Company.query.all()
        current_app.logger.info(f"Companies retrieved: {", ".join([str(company.id) for company in companies])}")
        return jsonify([company.to_dict() for company in companies]), 200

    except Exception as e:
        current_app.logger.error(f"Unexpected error in {get_companies.__name__}: {str(e)}")
        return jsonify(error="Internal server error"), 500



@companies_bp.route("/companies/<int:company_id>", methods=["PATCH"])
def edit_company(company_id):

    try:
        edited_company = db.get_or_404(Company, company_id)
        print(edited_company.name, edited_company.id)
        data = request.get_json()
        # Check if all the fields are valid:
        if any(key not in edited_company.editable_fields() for key in data):
            invalid_fields=[key for key in data if key not in edited_company.editable_fields()]
            current_app.logger.warning(f"Invalid field(s): {', '.join(invalid_fields)}")
            return jsonify(error=f"Invalid field(s): {", ".join(invalid_fields)} for company: {edited_company.name}."), 400
        # Check if the Name field is empty:
        if data.get("name") is None and data.get("name").strip() == "":
            current_app.logger.warning(f"Empty Name field while editing a Company")
            return jsonify(error="Product name cannot be empty."), 400
        # Check if Name, if being changed, is not already taken:
        if data["name"] != edited_company.name:
            if Company.query.filter_by(name=data["name"]).first():
                current_app.logger.warning(f"Not unique name for editing a Company")
                return jsonify(error="This name is already occupied by another Company."), 400
        # Apply changes:
        for key, value in data.items():
            # Set the attribute Name only when it is being changed, avoiding IntegrityError:
            if key != "name" or value != edited_company.name:
                setattr(edited_company, key, value)
        db.session.commit()
        current_app.logger.info(f"Correctly updated the Company: {edited_company.name}.")
        return jsonify(edited_company.to_dict()), 200


    except NotFound:
        current_app.logger.warning(f"Company with ID: {company_id} not found.")
        return jsonify(error=f"Company of ID: {company_id} not found."), 404

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Unexpected error in {edit_company.__name__}: {str(e)}")
        return jsonify(error="Internal server error"), 500

@companies_bp.route("/companies/<int:company_id>", methods=["DELETE"])
def delete_company(company_id):

    try:
        deleted_company = db.get_or_404(Company, company_id)
        db.session.delete(deleted_company)
        db.session.commit()
        current_app.logger.info(f"Company: {deleted_company.name} successfully deleted from the database.")
        return jsonify(success=f"Successfully deleted the company: {deleted_company.name}."), 200

    except NotFound:
        current_app.logger.warning(f"Company with ID: {company_id} not found.")
        return jsonify(error=f"Company of ID: {company_id} not found."), 404

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Unexpected error in {delete_company.__name__}: {str(e)}")
        return jsonify(error="Internal server error"), 500


@companies_bp.route("/companies", methods=["POST"])
def add_company():

    data = request.get_json()
    # Check if the keys from the body match the required ones:
    if any(key not in Company.editable_fields().keys() for key in data.keys()):
        current_app.logger.error("Unable to post a new company: invalid fields.")
        invalid_fields = [key for key in data if key not in Company.editable_fields().keys()]
        return jsonify(error=f"Invalid field(s): {", ".join(invalid_fields)}."), 400

    # Check if the Name from the form is not already occupied:
    if data.get("name") in [company.name for company in Company.query.all()]:
        current_app.logger.error("Unable to post a new company: name already taken.")
        return jsonify(error=f"The company of a name: {data["name"]} already exists."), 400

    # Check if the Name field is not empty:
    if data.get("name") is not None and data.get("name").strip() == "":
        return jsonify(error="Product name cannot be empty."), 400

    # Creating a new Company:
    try:
        new_company = Company()
        for key, value in data.items():
            setattr(new_company, key, value)

        new_company.user_id = 1
        db.session.add(new_company)
        db.session.commit()
        assign_company_to_user(company_id=new_company.id, user_id=new_company.user_id)
        current_app.logger.info(f"Successfully added a new company: {new_company.name} to the database.")
        return jsonify(success=f"Successfully created a new company: {new_company.name} (ID: {new_company.id})!"), 200

    except Exception as e:
        current_app.logger.error(f"Unexpected error in {add_company.__name__}: {str(e)}")
        return jsonify(error="Internal server error"), 500



