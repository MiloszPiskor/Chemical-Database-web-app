import re
from functools import wraps
from flask import jsonify, current_app, request
from models import Entry, LineItem
from datetime import datetime

def validate_json_payload(func):
    """Ensures request body contains only required fields."""
    @wraps(func)
    def wrapper_function(*args, **kwargs):

        data = request.get_json()
        # If there's no data or the data is not in the expected format
        if not data:
            return jsonify(error="No JSON data found in the request body."), 400

        if any(key not in Entry.REQUIRED_FIELDS for key in data.keys()):
            current_app.logger.error("Unable to post a new entry: invalid fields.")
            invalid_fields = [key for key in data if key not in Entry.REQUIRED_FIELDS]
            return jsonify(error=f"Invalid field(s): {", ".join(invalid_fields)} while trying to create a new entry."), 400

        kwargs['data'] = data
        return func(*args, **kwargs)

    return wrapper_function

def validate_document_nr(func):
    """Ensures that given document number is of a WZ format,
    which is ex. 'WZ 123/02/2025', meaning: WZ (document nr)/(month)/year)."""
    @wraps(func)
    def wrapper_function(*args, **kwargs):

        data = kwargs.get('data')

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
            if not (2000 <= year <= current_year <= current_year + 10):  # A reasonable time-frame for realistic inputs
                return False

            return True

        # Ensure that 'data' contains the required fields.
        if 'document_nr' not in data:
            current_app.logger.warning("Missing document number.")
            return jsonify(error="Document number is required."), 400

        if not validate_wz_number(data.get('document_nr')):
            current_app.logger.warning("Invalid document nr. format while trying to create new Entry.")
            return jsonify(
                error=f"Invalid document number format: {data.get('document_nr')}. The accepted format example"
                      f" for document nr.: 'WZ 123/02/2025', meaning: WZ (document nr)/(month)/year).")

        else:
            return func(*args, **kwargs)

    return wrapper_function

def validate_transaction_type(func):
    """Ensures that given transaction type is a 'Purchase' or 'Supply'"""
    @wraps(func)
    def wrapper_function(*args, **kwargs):

        data = kwargs.get('data')

        if data.get('transaction_type') not in Entry.TRANSACTION_TYPES:
            current_app.logger.warning("Invalid data for the transaction_type property of the Entry.")
            return jsonify(
                error=f"Invalid data in the 'transaction type' field. Should be {' or '.join(Entry.TRANSACTION_TYPES)}.")

        else:
            return func(*args, **kwargs)

    return wrapper_function


def validate_date_format(func):
    """Ensures that the given data is of the ISO 8601 format,
    meaning: YYYY-MM-DD"""
    @wraps(func)
    def wrapper_function(*args, **kwargs):

        data = kwargs.get('data')

        iso8601_date_regex = r"^\d{4}-\d{2}-\d{2}$"
        if not re.match(iso8601_date_regex, data.get('date')):
            current_app.logger.warning("Invalid date format while trying to add the new Entry.")
            return jsonify(
                error=f"Invalid date format: {data.get('date')} while adding new entry. The accepted date format is "
                      f"ISO 8601, meaning: YYYY-MM-DD")

        else:
            return func(*args, **kwargs)

    return wrapper_function

def validate_line_items(func):
    """Ensures that all the given LineItems are valid: contain
    all the required properties, actual Products existing in the
    database and appropriate values for their price and quantity"""
    @wraps(func)
    def wrapper_function(*args, **kwargs):

        data = kwargs.get('data')

        for line_item in data.get('line_items'):

            quantity = line_item.get('quantity')
            current_price = line_item.get('price_per_unit')

            if quantity is None or current_price is None:
                current_app.logger.warning(f"Fields 'quantity' or 'current_price' for LineItem are missing.")
                return jsonify(error="Fields 'quantity' or 'current_price' cannot be empty."), 400

            # Validate fields for LineItem:
            if any(key not in LineItem.REQUIRED_FIELDS for key in line_item):
                invalid_fields = [key for key in line_item if key not in LineItem.REQUIRED_FIELDS]
                current_app.logger.warning(
                    f"Invalid field(s): {', '.join(invalid_fields)} for the LineItem(s) while creating new Entry")
                return jsonify(
                    error=f"Invalid field(s): {', '.join(invalid_fields)} while trying to create new Entry."), 400
            # Check if the quantity and price fields are greater than 0:
            if float(quantity) <= 0 or float(current_price) <= 0:
                current_app.logger.warning(
                    f"Fields 'quantity' or 'current_price' for LineItem received nov-positive values.")
                return jsonify(error="Non-positive values for price or quantity for the product in the new Entry."), 400
            # Check if provided product field corresponds to the existing Product:
            # QUERYING DB MOVED TO VIEW FUNCTION

        return func(*args, **kwargs)

    return wrapper_function


