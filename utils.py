import os
from functools import wraps
import requests
from flask import jsonify, current_app, request, g, abort
from datetime import datetime

from werkzeug.exceptions import NotFound

from extensions import db
from models import Product, ProductCompany, Company
from users import get_or_create_user_from_token
import json
from dotenv import load_dotenv
from authlib.integrations.flask_client import OAuth
import jwt
from jwt.algorithms import RSAAlgorithm
from requests.exceptions import RequestException

# Loading the environment variables
load_dotenv()

def get_auth0_public_key():
    """Fetches Auth0's public key to verify JWTs (only once)."""
    url = f"https://{os.getenv('AUTH0_DOMAIN')}/.well-known/jwks.json"
    response = requests.get(url)
    jwks = response.json()["keys"]
    return {key["kid"]: RSAAlgorithm.from_jwk(json.dumps(key)) for key in jwks}  # Convert JWKS to a public key

AUTH0_PUBLIC_KEYS = get_auth0_public_key()

def product_check(name):
    """A function that checks if a product entered in the Product Form
    already exists in a database, if it does it redirects the User to the
    specific Product page"""
    check_for_product = Product.query.filter_by(name=name).first()
    return check_for_product

def get_user_item_or_404(model, item_id): # Instead of 3 for every model- worth considering
    """Retrieve an item (Product, Company, etc.) that belongs to the logged-in user. Return a 404 error if unauthorized."""
    item = model.query.filter_by(id=item_id, user_id=g.user.id).first()

    if item is None:
        error_message = f"Unauthorized or {model.__name__.lower()} not found!" # No Object ID in error message for security
        current_app.logger.error(f"Unauthorized or {model.__name__.lower()} with ID: {item_id} not found!")
        raise NotFound(description=error_message)
        # abort(404, description=f"Unauthorized or {model.__name__.lower()} not found!") # Global handler catches the error ( CHANGED FOR EASIER TESTABILITY AND DIRECT CONTROL OVER ERROR HANDLING IN VIEWS-- MORE SCALABLE )

    return item

def company_check(name):
    """A function that checks if a company entered in the Company Form
    already exists in a database."""
    check_for_company = Company.query.filter_by(name=name).first()
    return check_for_company

def single_line_item_validation(line_items_list):
    """Validate LineItems separately before DB transactions"""
    validated_line_items = []
        # Check if there is at least one LineItem tied to the new Entry:
    if isinstance(line_items_list, list) and len(line_items_list) > 0:
        for line_item in line_items_list:
            product_to_assign = Product.query.filter_by(name=line_item.get('product')).first()
            if not product_to_assign:
                current_app.logger.warning(f"Product '{line_item.get('product')}' does not exist in the database. Cannot create LineItem.")
                return jsonify(error=f"No such product: {line_item.get('product')} found in the database while trying to create new Entry"), 400
            validated_line_items.append(line_item)
        # One query to fetch all Product instances to avoid querying in the loop while creating LineItems, improving performance from N queries (per each product) to 1
    validated_products = {line_item["product"] : Product.query.filter_by(name=line_item["product"]).first() for line_item in validated_line_items}
    current_app.logger.info(f"Validated Line Items: {validated_products.keys()}, {validated_products.values()} ")

    return validated_line_items

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

def update_product_stock(product, transaction_type, quantity):
    """Update the product's stock based on the transaction type and quantity."""
    if transaction_type == "Purchase":
        product.stock += quantity
    elif transaction_type == "Supply":
        if product.stock < quantity:
            current_app.logger.error(f"Insufficient stock for product '{product.name}'. Current stock: {product.stock}, required: {quantity}")
            raise ValueError(f"Insufficient stock for product '{product.name}'. Current stock: {product.stock}, required: {quantity}")
        product.stock -= quantity
    current_app.logger.info(f"Updated stock for product '{product.name}': {product.stock}")

def validate_product_data(data, product_instance = None, is_update = False):
    """Validate product data before adding/updating a product."""

    # Check for invalid fields
    invalid_fields = [key for key in data if key not in Product.EDITABLE_FIELDS]
    if invalid_fields:
        current_app.logger.warning(f"Invalid fields: {invalid_fields}") if is_update else current_app.logger.error("Unable to post a new product: invalid fields.")
        return f"Invalid field(s): {', '.join(invalid_fields)}."

    # Check for empty required fields
    empty_fields = [key for key in Product.EDITABLE_FIELDS if key not in data or (isinstance(data[key], str) and data[key].strip() == "")]
    if empty_fields:
        return f"The following fields cannot be empty: {', '.join(empty_fields)}."

    # Check if name is being changed (for updates) or if the new name already exists
    new_name = data.get("name")
    if new_name:
        if is_update and product_instance and new_name != product_instance.name:
            current_app.logger.info(f"User attempting to rename product: {product_instance.name} to {new_name}. Checking availability...")
        if not is_update or (is_update and new_name != product_instance.name):
            if product_check(new_name):
                current_app.logger.warning(f"Product with name '{new_name}' already exists.")
                return "A product of this name already exists."

    return None  # Validation passed

def validate_company_data(data, company_instance = None, is_update = False):
    """Validate company data before adding/updating a company."""

    # Check if all the fields are valid:
    invalid_fields = [key for key in data if key not in Company.EDITABLE_FIELDS]
    if invalid_fields:
        current_app.logger.warning(f"Invalid field(s): {', '.join(invalid_fields)} while editing product.") if is_update\
            else current_app.logger.error(f"Unable to post a new company due to invalid fields: {', '.join(invalid_fields)}.")
        return f"Invalid field(s): {', '.join(invalid_fields)}."

    # Check any field is empty:
    missing_fields = [key for key in Company.EDITABLE_FIELDS if key not in data or (isinstance(data[key], str) and data[key].strip() == "")]
    if missing_fields:
        current_app.logger.warning("Empty fields for a Company model.")
        return f"The following fields cannot be empty: {', '.join(missing_fields)}."

    # Check if introduced name is not already taken:
    if (is_update and company_instance.name != data.get('name')) or not is_update:
        if is_update:
            current_app.logger.info(
                f"Attempting to rename company '{company_instance.name}' to '{data['name']}'. Checking availability...")

        if company_check(data.get('name')):
            current_app.logger.warning(f"Not unique name: {data["name"]} for editing a Company") if is_update \
                else current_app.logger.warning(f"Unable to post a new company: name {data['name']} already taken.")
            return "This name is already occupied by another Company."

def extra_user_info_call(token):
    """A function that fetches additional user information from Auth0."""
    try:
        user_info_url = f"https://{os.getenv('AUTH0_DOMAIN')}/userinfo"
        user_info_response = requests.get(user_info_url, headers={
            'Authorization': f'Bearer {token}'
        })
        s_code = user_info_response.status_code
        if s_code == 200:
            current_app.logger.info(f"Extra User info fetched successfully.")
            user_info = user_info_response.json()
            return user_info
        else:
            current_app.logger.error(f"Failed to fetch extra user info. Status code: {s_code}")
            return None

    except RequestException as e:
        current_app.logger.error(f"Network error occurred while fetching user info: {str(e)}")
        return None

    except Exception as e:
        current_app.logger.error(f"An error occurred while fetching extra user info: {str(e)}")
        return None

def requires_auth(f):

    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", None)
        if not auth_header:
            return jsonify({"error": "Authorization header is missing"}), 401

        parts = auth_header.split()
        if parts[0].lower() != "bearer":
            return jsonify({"error": "Authorization header must start with 'Bearer'"}), 401
        elif len(parts) != 2:
            return jsonify({"error": "Invalid Authorization header format"}), 401

        token = parts[1]
        try:
            unverified_header = jwt.get_unverified_header(token)
            key_id = unverified_header.get("kid")
            if key_id not in AUTH0_PUBLIC_KEYS:
                return jsonify({"error": "Invalid key ID"}), 401

            payload = jwt.decode(
                token,
                AUTH0_PUBLIC_KEYS[key_id],
                algorithms=["RS256"],
                audience=os.getenv("AUTH0_AUDIENCE"),
                issuer=f"https://{os.getenv('AUTH0_DOMAIN')}/",
            )
            # Fetch additional user info:
            user_info = extra_user_info_call(token = token)
            payload.update(user_info)  # Merge the user info into the payload

            request.user = payload
            # Sync the user with the database
            user = get_or_create_user_from_token()
            g.user = user # Store the user in the global context

        except jwt.ExpiredSignatureError:
            current_app.logger.error("Token expired")
            return jsonify({"error": "Token expired"}), 401

        except jwt.InvalidTokenError:
            current_app.logger.error("Invalid token")
            return jsonify({"error": "Invalid token"}), 401

        return f(*args, **kwargs)
    return decorated



