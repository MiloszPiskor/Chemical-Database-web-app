from flask import jsonify, current_app
from datetime import datetime
from extensions import db
from models import Product, ProductCompany

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