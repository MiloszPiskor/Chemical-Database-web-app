from functools import wraps
from sqlalchemy import text
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, Blueprint, current_app
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required, login_manager
from flask_ckeditor import CKEditor
from datetime import date
from werkzeug.exceptions import NotFound, BadRequest, InternalServerError
from models import User, Product, Company, LineItem, ProductCompany, db
from utils import validate_product_update, validate_product_data
from forms import ProductForm
import random
import os

products_bp = Blueprint("products", __name__)

def product_check(name):
    """A function that checks if a product entered in the Product Form
    already exists in a database, if it does it redirects the User to the
    specific Product page"""
    check_for_product = Product.query.filter_by(name=name).first()
    return check_for_product

def assign_user_to_product(product_id, user_id):
    try:
        product = Product.query.get(product_id)
        user = User.query.get(user_id)

        if not product:
            return jsonify(error="Product not found"), 404
        if not user:
            return jsonify(error="User not found"), 404

        product.user = user  # Assign the user using SQLAlchemy ORM
        db.session.commit()

        return jsonify(success=f"Product {product_id} assigned to user {user_id}"), 200

    except Exception as e:
        db.session.rollback()
        return jsonify(error=str(e)), 500

@products_bp.route("/products/<product_id>")
def get_product(product_id):

    try:
        product = db.get_or_404(Product, product_id)
        current_app.logger.info(f"Product retrieved: {product.id} by func: {get_product.__name__}")
        return jsonify(product=product.to_dict()), 200

    except NotFound:
        current_app.logger.warning(f"Product with ID: {product_id} not found.")
        return jsonify(error=f"Product of ID: {product_id} not found."), 404

    except Exception as e:
        current_app.logger.error(f"Unexpected error in {get_product.__name__}: {str(e)}")
        return jsonify(error="Internal server error"), 500

@products_bp.route("/products")
def get_products():

    user = User.query.get(1)
    print(f"User products:{user.products}")
    try:
        products = user.products
        current_app.logger.info(f"Products retrieved: {", ".join([str(product.id) for product in products])} by func: {get_product.__name__}")
        return jsonify([product.to_dict() for product in products]), 200

    except Exception as e:
        current_app.logger.error(f"Unexpected error in {get_products.__name__}: {str(e)}")
        return jsonify(error="Internal server error"), 500

@products_bp.route("/products/<product_id>", methods=["PATCH"])
def edit_product(product_id):

    try:
        edited_product = db.get_or_404(Product, product_id)
        print(edited_product.name, edited_product.id)
        data = request.get_json()
        # Validation of the json payload:
        validation_error = validate_product_data(data=data, is_update=True, product_instance= edited_product)
        if validation_error:
            return jsonify(error=validation_error), 400
        # Applying changes:
        for key, value in data.items():
            if key != "name" or (key == 'name' and value != edited_product.name):
                setattr(edited_product, key, value)
        db.session.commit()
        current_app.logger.info(f"Correctly updated the Product: {edited_product.name}.")
        return jsonify(edited_product.to_dict()), 200

    except NotFound:
        current_app.logger.warning(f"Product with ID: {product_id} not found.")
        return jsonify(error=f"Product of ID: {product_id} not found."), 404

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Unexpected error in {edit_product.__name__}: {str(e)}")
        return jsonify(error="Internal server error"), 500

@products_bp.route("/products/<product_id>", methods=["DELETE"])
def delete_product(product_id):

    try:
        deleted_product = db.get_or_404(Product, product_id)
        db.session.delete(deleted_product)
        db.session.commit()
        current_app.logger.info(f"Product: {deleted_product.name} successfully deleted from the database.")
        return jsonify(success=f"Successfully deleted the product: {deleted_product.name}."), 200

    except NotFound:
        current_app.logger.warning(f"Product with ID: {product_id} not found.")
        return jsonify(error=f"Product of ID: {product_id} not found."), 404

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Unexpected error in {delete_product.__name__}: {str(e)}")
        return jsonify(error="Internal server error"), 500

@products_bp.route("/products", methods=["POST"])
def add_product():

    data = request.get_json()
    # Validation of the json payload:
    validation_error = validate_product_data(data = data, is_update=False)
    if validation_error:
        return jsonify(error=validation_error), 400
    # Creating a new Product:
    try:
        new_product = Product()
        for key, value in data.items():
            setattr(new_product, key, value)
        # Set stock to 0
        setattr(new_product,"stock", 0)
        new_product.user_id = 1
        db.session.add(new_product)
        db.session.commit()
        assign_user_to_product(new_product.id, new_product.user_id)
        current_app.logger.info(f"Successfully added a new product: {new_product.name} to the database.")
        return jsonify(success=f"Successfully created a new product: {new_product.name} (ID: {new_product.id})!"), 200

    except Exception as e:
        current_app.logger.error(f"Unexpected error in {add_product.__name__}: {str(e)}")
        return jsonify(error="Internal server error"), 500
