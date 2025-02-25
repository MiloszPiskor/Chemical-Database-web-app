from flask import jsonify, current_app
from sqlalchemy.exc import SQLAlchemyError
from extensions import db
from models import Entry, Company, LineItem, Product, User
from utils import get_or_create_product_company, calculate_product_company, single_line_item_validation, update_product_stock

class EntryService:

    @staticmethod
    def pre_entry_validation(data, user):
        """Validation function handling appropriate DB queries."""
        try:
            # Ensure document_nr is unique
            if Entry.query.filter_by(document_nr=data.get("document_nr")).first():
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

            # Check if validation returned a response (error case)
            if isinstance(validated_line_items, tuple):  # Flask responses return (jsonify(), status_code)
                return validated_line_items  # Directly return the error response

            return EntryService.save_entry(data, validated_line_items, company_to_assign, user)

        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error while creating new entry: {str(e)}")
            return jsonify(error="An internal database error occurred. Please try again later."), 500

        except Exception as e:
            current_app.logger.error(f"Unexpected error in {EntryService.pre_entry_validation.__name__}: {str(e)}")
            return jsonify(error="Internal server error"), 500

    @staticmethod
    def save_entry(data, validated_line_items, company_to_assign, user):
        """Handles database operations separately from validation."""
        try:
            # SETTING THE ATTRIBUTES FOR THE NEW ENTRY
            new_entry = Entry()
            for key, value in data.items():
                if key != "line_items" and key != "company":
                    setattr(new_entry, key, value)

            # Assigning the Entry to the User and Company
            new_entry.user = user
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

        except ValueError as e:
            db.session.rollback()
            return jsonify(error=f"Failed to save entry : {e}"), 400

        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Error saving entry: {str(e)}")
            return jsonify(error="Failed to save entry."), 500

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error in {EntryService.save_entry}: {str(e)}")
            return jsonify(error="Internal server error."), 500



    @staticmethod
    def process_line_items(new_entry, validated_line_items, company_to_assign):
        """Handles processing and saving line items."""
        try:
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

                # Handle Product's Stock
                try:
                    update_product_stock(
                        product=product_obj,
                        transaction_type=new_entry.transaction_type,
                        quantity=line_item["quantity"]
                    )
                    current_app.logger.info(f"Updated stock for product: {product_name}. Current stock: {product_obj.stock}")
                except ValueError as e:
                    db.session.rollback()
                    current_app.logger.error(f"Value Error in product stock update: {str(e)}")
                    raise

        except Exception as e:
            current_app.logger.error(f"Error processing line items: {str(e)}")
            db.session.rollback()
            raise  # Re-raise to propagate to the outer try/except