from flask import jsonify, current_app
from sqlalchemy.exc import SQLAlchemyError
from extensions import db
from models import Entry, Company, LineItem, Product, User
from utils import get_or_create_product_company, calculate_product_company, single_line_item_validation

class EntryService:

    @staticmethod
    def pre_entry_validation(data):
        """Validation function handling appropriate DB queries."""
        try:
            # Ensure document_nr is unique
            if db.session.query(Entry).filter_by(document_nr=data["document_nr"]).first():
                current_app.logger.error(
                    f"Unable to post a new entry: entry tied with a transaction number: {data.get('document_nr')} already exists.")
                return jsonify(error=f"The entry tied to a transaction: {data.get('document_nr')} already exists."), 400

            # Ensure the Company exists
            company_to_assign = Company.query.filter_by(name=data.get('company')).first()
            if not company_to_assign:
                current_app.logger.warning(f"Company: {data.get('company')} not found.")
                return jsonify(error=f"Company: {data.get('company')} not found in the database."), 400

            # Validate LineItems
            validated_line_items = single_line_item_validation(data.get('line_items'))

            return EntryService.save_entry(data, validated_line_items, company_to_assign)

        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error while creating new entry: {str(e)}")
            return jsonify(error="An internal database error occurred. Please try again later."), 500

    @staticmethod
    def save_entry(data, validated_line_items, company_to_assign):
        """Handles database operations separately from validation."""
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

            # Process LineItems
            EntryService.process_line_items(new_entry, validated_line_items, company_to_assign)

            db.session.commit()
            current_app.logger.info(f"Successfully created a new Entry: {new_entry.id}!")
            print(f"Successfully created a new Entry: {new_entry.id}!")
            return jsonify(message="Entry created successfully!", entry_id=new_entry.id), 201

        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Error saving entry: {str(e)}")
            return jsonify(error="Failed to save entry."), 500

    @staticmethod
    def process_line_items(new_entry, validated_line_items, company_to_assign):
        """Handles processing and saving line items."""
        validated_products = {
            line_item["product"]: Product.query.filter_by(name=line_item["product"]).first()
            for line_item in validated_line_items
        }

        for line_item in validated_line_items:
            product_name = line_item["product"]
            product_obj = validated_products[product_name]

            new_line_item = LineItem(
                quantity=line_item["quantity"],
                price_per_unit=line_item["price_per_unit"],
                product=product_obj,
                entry=new_entry
            )
            db.session.add(new_line_item)

            # Prevent duplicate references in Product.line_items
            if new_line_item not in product_obj.line_items:
                product_obj.line_items.append(new_line_item)
                print(f"Appended Line Items for product: {product_name}. Their current list: {product_obj.line_items}")

            # Handle ProductCompany updates
            existing_connection = get_or_create_product_company(product_obj.id, company_to_assign.id)
            calculate_product_company(
                product_company=existing_connection,
                transaction_type=new_entry.transaction_type,
                quantity=line_item["quantity"]
            )

            current_app.logger.info(f"Updated ProductCompany balance for ID: {existing_connection.id}.")