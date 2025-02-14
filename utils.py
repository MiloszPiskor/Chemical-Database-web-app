from flask import jsonify, current_app
from datetime import datetime
from extensions import db
from models import Product, ProductCompany

def product_check(name):
    """A function that checks if a product entered in the Product Form
    already exists in a database, if it does it redirects the User to the
    specific Product page"""
    check_for_product = Product.query.filter_by(name=name).first()
    return check_for_product

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

def validate_product_update(data, edited_product):
    """Helper function to validate product update fields"""
    # Check if attribute not in Product attributes:
    if any(key not in edited_product.editable_fields() for key in data):
        invalid_fields = [key for key in data if key not in edited_product.editable_fields().keys()]
        current_app.logger.warning(f"Invalid fields: {invalid_fields}")
        return f"Invalid field(s): {', '.join(invalid_fields)}."

    # Check if the name property is going to be changed, and if new one is unique:
    if data.get("name") and data.get("name") != edited_product.name:
        current_app.logger.info(f"User changing the name of the product: {edited_product.name} to {data['name']}.\n"
                                    f"Checking for name availability...")
        # Check for Existing Product of the entered name:
        if Product.query.filter_by(name=data["name"]).first():
            current_app.logger.warning(f"Product of name: {data['name']} already exists.")

            return "A product of this name already exists."
    # Check if required fields are not not empty
    for field in edited_product.editable_fields():
        value = data.get(field)
        if value is None or (isinstance(value, str) and value.strip() == ""):
            return f"{field.capitalize()} cannot be empty."

    return None

def validate_product_data(data, product_instance=None, is_update=False):
    """Validate product data before adding/updating a product.

    Args:
        data (dict): The request payload containing product details.
        product_instance (Product, optional): The existing product instance for updates. Defaults to None.
        is_update (bool): Whether the operation is an update. Defaults to False.

    Returns:
        tuple or None: (error_message, status_code) if validation fails, None if valid.
    """
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