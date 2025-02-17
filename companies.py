from functools import wraps
from flask import Flask, request, redirect, url_for, flash, jsonify, Blueprint, current_app, g
from werkzeug.exceptions import NotFound
from datetime import date
from models import User, Product, Company, LineItem, ProductCompany, db
from forms import RegisterForm, LoginForm, EntryForm, CompanyForm, ProductForm
from utils import validate_company_data, requires_auth, get_user_company_or_404
from users import get_or_create_user_from_token
from dotenv import load_dotenv
import os
import logging

companies_bp = Blueprint("companies", __name__)

# with app.app_context():
#     if not current_app.debug:  # Ensure logging in production mode
#         current_app.logger.setLevel(logging.INFO)

@companies_bp.route("/companies/<int:company_id>")
def get_company(company_id):

    try:
        company = db.get_or_404(Company, company_id)
        current_app.logger.info(f"Company retrieved: {company.id} by func: {get_company.__name__}")
        return jsonify(company=company.to_dict()), 200

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
        user = User.query.get(1)
        companies = user.companies
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

        # Validate the json payload:
        validation_error = validate_company_data(data = data, is_update = True, company_instance = edited_company)
        if validation_error:
            return jsonify(error=validation_error), 400

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
@requires_auth
def add_company():

    data = request.get_json()

    # Validate the json payload:
    validation_error = validate_company_data(data = data, is_update = False)
    if validation_error:
        return jsonify(error=validation_error), 400

    # Creating a new Company:
    try:
        new_company = Company()
        for key, value in data.items():
            setattr(new_company, key, value)

        # Handling User:
        user = g.user
        new_company.user = user
        # Committing the changes:
        db.session.add(new_company)
        db.session.commit()
        current_app.logger.info(f"Successfully added a new company: {new_company.name} to the database.")
        return jsonify(success=f"Successfully created a new company: {new_company.name} (ID: {new_company.id})!"), 200

    except Exception as e:
        current_app.logger.error(f"Unexpected error in {add_company.__name__}: {str(e)}")
        return jsonify(error="Internal server error"), 500



