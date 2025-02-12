from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, Blueprint, current_app
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import NotFound
from models import User, Product, Company, Entry, LineItem, ProductCompany, db
from validator_funcs import validate_json_payload, validate_document_nr, validate_transaction_type, validate_date_format, validate_line_items
from EntryService import EntryService
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
        f"Entries retrieved: {", ".join([str(entry.id) for entry in entries])} by func: {get_entries.__name__}") # May consider if it's not hindering the performance of the code
        print(f"Line items of each : {", ".join([str(entry.line_items) for entry in entries])}")
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
    # NOT ENABLED DUE TO ENTRIES BEING IMMUTABLE- LEGAL & COMPLIANCE RISKS-
    # MIGHT CONSIDER IMPLEMENTING CORRECTIONAL ENTRIES (IN CASE OF A USER ERROR)
    # RELATED TO THE ORIGINAL ONE
    pass

@entries_bp.route("/entries", methods=["POST"])
@validate_json_payload
@validate_document_nr
@validate_transaction_type
@validate_date_format
@validate_line_items
def add_entry(*args, **kwargs):
    """Handles entry validation and creation."""
    data = kwargs.get('data')
    return EntryService.pre_entry_validation(data)













# This has been detached and modularized into EntryService methods:
# @entries_bp.route("/entries", methods=["POST"])
# @validate_json_payload
# @validate_document_nr
# @validate_transaction_type
# @validate_date_format
# @validate_line_items
# def pre_entry_validation():
#     """Validation function handling appropriate DB queries. It cleans and extracts necessary data
#     alongside with the decorators to pass it into function that handles entry creation."""
#
#     data = request.get_json()  # This happens only once now, then gets passed to all decorators
#
#     # Ensure document_nr is unique
#     if db.session.query(Entry).filter_by(document_nr=data["document_nr"]).first():
#         current_app.logger.error(
#         f"Unable to post a new entry: entry tied with a transaction number: {data.get('document_nr')} already exists.")
#         return jsonify(error=f"The entry tied to a transaction: {data.get('document_nr')} already exists."), 400
#
#     # Ensure the Company exists (if provided)(lookup in existing Companies front preferred):
#     company_to_assign = Company.query.filter_by(name=data.get('company')).first() # user.companies after Okta validation implemented (User ID fetched from JWT Token)
#     if not company_to_assign:
#         current_app.logger.warning(f"Company: {data.get('company')} introduced while creating new Entry does not exist.")
#         return jsonify(error=f"Company: {data.get('company')} not found in the database.")
#
#     # Validate LineItems (and query the relevant products)
#     validated_line_items = single_line_item_validation(data.get('line_items'))
#     return create_entry(data, validated_line_items, company_to_assign)
#
# def create_entry(data, validated_line_items, company_to_assign):
#     try:
#         # SETTING THE ATTRIBUTES FOR THE NEW ENTRY
#         new_entry = Entry()
#         for key, value in data.items():
#             if key != "line_items" and key != "company":
#                 setattr(new_entry, key, value)
#
#         # Assigning the Entry to the User and Company
#         new_entry.user = User.query.get(1)
#         new_entry.company = company_to_assign
#         db.session.add(new_entry)
#         current_app.logger.info(f"Adding new Entry: {new_entry.id} to the register.")
#         db.session.flush()
#
#         # Create and add validated LineItems:
#         validated_products = {line_item["product"]: Product.query.filter_by(name=line_item["product"]).first() for
#                               line_item in validated_line_items}
#         for line_item in validated_line_items:
#             product_name = line_item["product"]
#             product_obj = validated_products[product_name]
#
#             new_line_item = LineItem(
#                 quantity=line_item["quantity"],
#                 price_per_unit=line_item["price_per_unit"],
#                 # Assigning LineItem to the Product:
#                 product=product_obj,
#                 # Assigning LineItem to the Entry:
#                 entry=new_entry
#             )
#             db.session.add(new_line_item)
#
#             # Updating line_items of a Product
#             if new_line_item not in product_obj.line_items: # Prevent duplication
#                 product_obj.line_items.append(new_line_item)
#             current_app.logger.info(f"Appended Line Items for product: {product_name}. Their current list: {product_obj.line_items}")
#             print(f"Appended Line Items for product: {product_name}. Their current list: {product_obj.line_items}")
#             # Create and add ProductCompanies:
#             existing_connection = get_or_create_product_company(product_obj.id, company_to_assign.id)
#             calculate_product_company(
#                 product_company = existing_connection,
#                 transaction_type = data.get('transaction_type'),
#                 quantity = line_item["quantity"]
#             )
#             current_app.logger.info(f"Successfully updated balances for the ProductCompany: {existing_connection.id}.")
#
#         db.session.commit()
#         current_app.logger.info(f"Successfully created a new Entry: {new_entry.id}!")
#         print(f"Successfully created a new Entry: {new_entry.id}!")
#         return jsonify(message="Entry created successfully!"), 201
#
#     except SQLAlchemyError as e:
#         db.session.rollback()
#         current_app.logger.error(f"Database error while creating new entry: {str(e)}")
#         return jsonify(error="An internal database error occurred. Please try again later."), 500

