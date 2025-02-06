from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, Blueprint, current_app
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import NotFound
from models import User, Product, Company, Entry, LineItem, ProductCompany, db
from dotenv import load_dotenv
import os
import logging
from datetime import datetime
import re

entries_bp = Blueprint("entries", __name__)

def assign_entry_to_user(user_id, entry_id):
    try:
        entry = Entry.query.get(entry_id)
        user = User.query.get(user_id)

        if not entry:
            return jsonify(error="Entry not found"), 404
        if not user:
            return jsonify(error="User not found"), 404

        entry.user = user  # Assign the user using SQLAlchemy ORM
        db.session.commit()

        return jsonify(success=f"Entry {entry_id} assigned to user {user_id}"), 200

    except Exception as e:
        db.session.rollback()
        return jsonify(error=str(e)), 500

def validate_wz_number(wz_number):
    """Function validating document_nr field for Entry creation. Ensures the data is in the proper format of:
    ex. WZ 123/02/2025, meaning WZ (doc_nr)/(month)/(year)."""

    match = re.match(r"^WZ\s(\d{1,4})/(\d{1,2})/(\d{4})$", wz_number)
    if not match:
        return False

    transaction, month, year = map(int, match.groups())

    if not (1 <= month <= 12):
        return False

    current_year = datetime.now().year
    if not (2000 <= year <= current_year <= current_year + 10): # A reasonable time-frame for realistic inputs
        return False

    return True

def validate_line_item(line_item):

    quantity = line_item.get('quantity')
    current_price = line_item.get('current_price')

    if quantity is None or current_price is None:
        current_app.logger.warning(f"Fields 'quantity' or 'current_price' for LineItem are missing.")
        return jsonify(error="Fields 'quantity' or 'current_price' cannot be empty."), 400

    # Validate fields for LineItem:
    if any(key not in LineItem.REQUIRED_FIELDS for key in line_item):
        invalid_fields=[key for key in line_item if key not in LineItem.REQUIRED_FIELDS]
        current_app.logger.warning(f"Invalid field(s): {', '.join(invalid_fields)} for the LineItem(s) while creating new Entry")
        return jsonify(error=f"Invalid field(s): {', '.join(invalid_fields)} while trying to create new Entry."), 400
    # Check if the quantity and price fields are greater than 0:
    if float(quantity) <= 0 or float(current_price) <= 0:
        current_app.logger.warning(f"Fields 'quantity' or 'current_price' for LineItem received nov-positive values.")
        return jsonify(error="Non-positive values for price or quantity for the product in the new Entry."), 400
    # Check if provided product field corresponds to the existing Product:
    product_to_assign = Product.query.filter_by(name=line_item.get('product')).first()
    if not product_to_assign:
        current_app.logger.warning(f"Product '{line_item.get('product')}' does not exist in the database. Cannot create LineItem.")
        return jsonify(error=f"No such product: {line_item.get('product')} found in the database while trying to create new Entry"), 400

def get_or_create_product_company(product_id, company_id):

    try:
        existing_connection = ProductCompany.query.filter_by(product_id= product_id, company_id=company_id).first()
        if existing_connection:
            current_app.logger.info(f"Successfully fetched existing ProductCompany: {existing_connection.id} connection. ")
            return  existing_connection
        else:
            today = datetime.today()
            new_connection = ProductCompany(
                company_id = company_id,
                product_id = product_id,
                total_quantity_supplied = 0,
                total_quantity_bought = 0,
                last_transaction_date = today.strftime("%Y-%m-%d")
            )
            db.session.add(new_connection)
            db.session.flush() # In case the code fails before the final Entry commit
            current_app.logger.info(f"Successfully created new ProductCompany for Company: {company_id} and Product: {product_id}.")
            return new_connection
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"An error: {str(e)} occurred while creating new ProductCompany model.")
        raise RuntimeError(f"Database error: {str(e)}")

def calculate_product_company(product_company, transaction_type, quantity):
    if transaction_type == "Purchase":
        product_company.total_quantity_bought += quantity
    elif transaction_type == "Supply":
        product_company.total_quantity_supplied += quantity


# with app.app_context():
#     if not current_app.debug:  # Ensure logging in production mode
#         current_app.logger.setLevel(logging.INFO)

@entries_bp.route("/entries/<int:entry_id>")
def get_entry(entry_id):

    try:
        entry = db.get_or_404(Entry, entry_id)
        print(entry.line_items) # Debug line
        current_app.logger.info(f"Entry retrieved: {entry.id} by func: {get_entry.__name__}")
        return jsonify(entry=entry.to_dict()), 200

    except NotFound:
        current_app.logger.warning(f"Entry with ID: {entry_id} not found.")
        return jsonify(error=f"Entry of ID: {entry_id} not found."), 404

    except Exception as e:
        current_app.logger.error(f"Unexpected error in {get_entry.__name__}: {str(e)}")
        return jsonify(error="Internal server error"), 500

@entries_bp.route("/entries")
def get_entries():

    try:
        entries = Entry.query.all()
        current_app.logger.info(
        f"Entries retrieved: {", ".join([entry.id for entry in entries])} by func: {get_entries.__name__}") # May consider if it's not hindering the performance of the code
        return jsonify([entry.to_dict() for entry in entries]), 200
    except Exception as e:
        current_app.logger.error(f"Unexpected error in {get_entries.__name__}: {str(e)}")
        return jsonify(error="Internal server error"), 500


@entries_bp.route("/entries/<int:entry_id>", methods=["PATCH"])
def edit_entry(entry_id):
    # NOT ENABLED DUE TO ENTRIES BEING IMMUTABLE- LEGAL & COMPLIANCE RISKS-
    # MIGHT CONSIDER IMPLEMENTING CORRECTIONAL ENTRIES (IN CASE OF A USER ERROR)
    # RELATED TO THE ORIGINAL ONE
    pass

@entries_bp.route("/entries/<int:entry_id>", methods=["DELETE"])
def delete_entry(entry_id):

    pass

@entries_bp.route("/entries", methods=["POST"])
def add_entry():

    data = request.get_json()
    # Check if the keys from the body match the required ones:
    if any(key not in Entry.REQUIRED_FIELDS for key in data.keys()):
        current_app.logger.error("Unable to post a new entry: invalid fields.")
        invalid_fields = [key for key in data if key not in Entry.REQUIRED_FIELDS]
        return jsonify(error=f"Invalid field(s): {", ".join(invalid_fields)} while trying to create a new entry."), 400

    # Check if the document_nr from the form is unique:
    if db.session.query(Entry).filter_by(document_nr=data["document_nr"]).first():
        current_app.logger.error(f"Unable to post a new entry: entry tied with a transaction number: {data.get('document_nr')} already exists.")
        return jsonify(error=f"The entry tied to a transaction: {data.get('document_nr')} already exists."), 400

    # Check if entered Company exists (lookup in existing Companies front preferred):
    company_to_assign = Company.query.filter_by(name=data.get('company')).first() # user.companies after Okta validation implemented (User ID fetched from JWT Token)
    if not company_to_assign:
        current_app.logger.warning(f"Company: {data.get('company')} introduced while creating new Entry does not exist.")
        return jsonify(error=f"Company: {data.get('company')} not found in the database.")

    # Check if transaction_type field has received valid data (also lookup from possible ones preferred in front):
    if data.get('transaction_type') not in Entry.TRANSACTION_TYPES:
        current_app.logger.warning("Invalid data for the transaction_type property of the Entry.")
        return jsonify(error=f"Invalid data in the 'transaction type' field. Should be {' or '.join(Entry.TRANSACTION_TYPES)}.")
    # Check if date format is ISO 8601:
    iso8601_date_regex = r"^\d{4}-\d{2}-\d{2}$"
    if not re.match(iso8601_date_regex, data.get('date')):
        current_app.logger.warning("Invalid date format while trying to add the new Entry.")
        return jsonify(error=f"Invalid date format: {data.get('date')} while adding new entry. The accepted date format is "
                             f"ISO 8601, meaning: YYYY-MM-DD")
    # Maybe Regex to validate transaction_nr format (validate_wz_number function):
    if not validate_wz_number(data.get('document_nr')):
        current_app.logger.warning("Invalid document nr. format while trying to create new Entry.")
        return jsonify(error=f"Invalid document number format: {data.get('document_nr')}. The accepted format example"
                             f" for document nr.: 'WZ 123/02/2025', meaning: WZ (document nr)/(month)/year).")

    # Validate LineItems separately before DB transactions
    line_items = data.get("line_items", [])
    validated_line_items = []
    # Check if there is at least one LineItem tied to the new Entry:
    if isinstance(line_items, list) and len(line_items) > 0:
        for line_item in line_items:
            validated_line_items.append(line_item)
    # One query to fetch all Product instances to avoid querying in the loop while creating LineItems, improving performance from N queries (per each product) to 1
    validated_products = {line_item["product"] : Product.query.filter_by(name=line_item["product"]).first() for line_item in validated_line_items}
    current_app.logger.info(f"Validated Line Items: {validated_products.keys()}, {validated_products.values()} ")
    # Create new Entry after successful validation:
    try:
        # SETTING THE ATTRIBUTES FOR THE NEW ENTRY
        new_entry = Entry()
        for key, value in data.items():
            if key != "line_items" and key != "company":
                setattr(new_entry, key, value)

        # Assigning the Entry to the User and Company
        new_entry.user = User.query.get(1)
        new_entry.company = company_to_assign
        db.session.add(new_entry)
        current_app.logger.info(f"Adding new Entry: {new_entry.id} to the register.")
        db.session.flush()

        # Create and add validated LineItems:
        for line_item in validated_line_items:
            product_name = line_item["product"]
            product_obj = validated_products[product_name]
            new_line_item = LineItem(
                quantity=line_item["quantity"],
                price_per_unit=line_item["price_per_unit"],
                # Assigning LineItem to the Product:
                product=product_obj,
                # Assigning LineItem to the Entry:
                entry=new_entry
            )
            db.session.add(new_line_item)

            # Updating line_items of a Product
            if new_line_item not in product_obj.line_items: # Prevent duplication
                product_obj.line_items.append(new_line_item)
            current_app.logger.info(f"Appended Line Items for product: {product_name}. Their current list: {product_obj.line_items}")
            print(f"Appended Line Items for product: {product_name}. Their current list: {product_obj.line_items}")
            # Create and add ProductCompanies:
            existing_connection = get_or_create_product_company(product_obj.id, company_to_assign.id)
            calculate_product_company(
                product_company = existing_connection,
                transaction_type = data.get('transaction_type'),
                quantity = line_item["quantity"]
            )
            current_app.logger.info(f"Successfully updated balances for the ProductCompany: {existing_connection.id}.")

        db.session.commit()
        current_app.logger.info(f"Successfully created a new Entry: {new_entry.id}!")
        print(f"Successfully created a new Entry: {new_entry.id}!")
        return jsonify(message="Entry created successfully!"), 201

    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error while creating new entry: {str(e)}")
        return jsonify(error="An internal database error occurred. Please try again later."), 500

