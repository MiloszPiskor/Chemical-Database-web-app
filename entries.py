from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, Blueprint, current_app
from flask_sqlalchemy import SQLAlchemy
from werkzeug.exceptions import NotFound
from models import User, Product, Company, Entry, LineItem, ProductCompany, db
from dotenv import load_dotenv
import os
import logging
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

# with app.app_context():
#     if not current_app.debug:  # Ensure logging in production mode
#         current_app.logger.setLevel(logging.INFO)

@entries_bp.route("/entries/<int:entry_id>")
def get_entry(entry_id):

    pass

@entries_bp.route("/entries")
def get_entries():

    pass

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
        return jsonify(error=f"Invalid field(s): {", ".join(invalid_fields)}."), 400

    # Check if the document_nr from the form is unique:
    if db.session.query(Entry).filter_by(document_nr=data["document_nr"]).first():
        current_app.logger.error(f"Unable to post a new entry: entry tied with a transaction number: {data.get('document_nr')} already exists.")
        return jsonify(error=f"The entry tied to a transaction: {data.get('document_nr')} already exists."), 400

    # Check if there is at least one LineItem tied to the new Entry:
    if isinstance(data.get("line_items"), list) and len(data.get("line_items")) > 0:
        # Validate the structure of the provided LineItems:
        line_items = data.get("line_items")
        for line_item in line_items:
            if any(key not in LineItem.REQUIRED_FIELDS for key in line_item):
                invalid_fields=[key for key in line_item if key not in LineItem.REQUIRED_FIELDS]
                current_app.logger.warning(f"Invalid field(s): {', '.join(invalid_fields)} for the LineItem(s) while creating new Entry")
                return jsonify(error=f"Invalid field(s): {', '.join(invalid_fields)} while trying to create new Entry."), 400
            # Check if the quantity and price fields are greater than 0:
            if line_item.get('quantity') <= 0 or line_item.get('current_price') <= 0:
                current_app.logger.warning(f"Fields 'quantity' or 'current_price' for LineItem received nov-positive values.")
                return jsonify(error="Non-positive values for price or quantity for the product in the new Entry."), 400
            # Check if provided product field corresponds to the existing Product:
            if not Product.query.filter_by(name=line_item.get('product')).first():
                current_app.logger.warning(f"Field 'product' for LineItem received non-existing Product.")
                return jsonify(error=f"No such product: {line_item.get('product')} found in the database while trying to create new Entry"), 400
            # Create LineItem(s):


    # Check if entered Company exists (lookup in existing Companies front preferred):
    if data.get('company') not in #user.companies

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
    # Maybe Regex to validate transaction_nr format:
