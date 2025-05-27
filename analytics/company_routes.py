from sqlalchemy import func
from sqlalchemy.orm import joinedload
from analytics import analytics_bp
from analytics.utils import count_transactions, sum_monetary_totals, query_results, calculate_transaction_stats
from models import ProductCompany, Product, Company, Entry, LineItem
from flask import jsonify, current_app, g
from werkzeug.exceptions import NotFound
from extensions import db
from utils import get_user_item_or_404, requires_auth

def fetch_product_history(company_id):
    """
    Helper function that builds a query for all ProductCompany entries related to a given company.

    Applies a filter by company_id and uses eager loading to join the related Product data
    to optimize access to product details.

    Returns a SQLAlchemy query object (not yet evaluated).
    """
    return (
        db.session.query(ProductCompany)
        .filter(ProductCompany.company_id == company_id)
        .options(joinedload(ProductCompany.product)) # eager loading of the product for its data
    )

@analytics_bp.route("/companies/<company_id>/products", methods=["GET"])
@requires_auth
def all_company_products(company_id):
    """
    Retrieves a list of all products associated with a given company, ordered by the most recent
    transaction date.

    This endpoint provides a summary of each product's quantities purchased,
    quantities supplied, and the last transaction date.

    Returns a JSON response containing company information and product details,
    including product ID, name, image URL, and quantities.
    """

    try:
        company = get_user_item_or_404(Company, company_id)

        all_products_query = (
            fetch_product_history(company_id)
            .order_by(ProductCompany.last_transaction_date.desc())
            .all()
        )
        # Calculate totals for each company
        # total_purchase_amount = sum(pc.total_quantity_bought for pc in all_products_query)
        # total_supply_amount = sum(pc.total_quantity_supplied for pc in all_products_query)

        # Count how many purchase/supply entries this company has:
        entries = query_results(company_id = company.id)

        stats = calculate_transaction_stats(entries = entries, pcs = all_products_query)

        # transactions_count = count_transactions(entries_list= entries)
        # purchase_count = transactions_count["purchase"]
        # supply_count = transactions_count["supply"]
        #
        # # Total monetary value across all line‐items of that company:
        # monetary_totals = sum_monetary_totals(entries_list = entries)
        # total_value_purchased = monetary_totals["purchase"]
        # total_value_supplied = monetary_totals["supply"]
        #
        # # Averages per transaction (accounting for zero count)
        # average_quantity_per_purchase = round(total_purchase_amount / purchase_count, 2) if purchase_count else 0
        # average_quantity_per_supply   = round(total_supply_amount  / supply_count,   2) if supply_count   else 0
        #
        # average_value_per_purchase = round(total_value_purchased / purchase_count, 2) if purchase_count else 0
        # average_value_per_supply   = round(total_value_supplied  / supply_count,   2) if supply_count   else 0

        return jsonify({
            "company": {
                "id": company.id,
                "name": company.name
            },
             "stats": stats, # {
            #     "transaction_counts": {
            #         "purchase": purchase_count,
            #         "supply":   supply_count
            #     },
            #     "totals": {
            #         "quantitative": {
            #             "purchased": total_purchase_amount,
            #             "supplied":  total_supply_amount
            #         },
            #         "monetary": {
            #             "purchased": total_value_purchased,
            #             "supplied":  total_value_supplied
            #         }
            #     },
            #     "average_quantity_per_transaction": {
            #         "purchase": average_quantity_per_purchase,
            #         "supply":   average_quantity_per_supply
            #     },
            #     "average_value_per_transaction": {
            #         "purchase": average_value_per_purchase,
            #         "supply":   average_value_per_supply
            #     }
            # },
            "products": [
                {
                    "product_id": pc.product.id,
                    "product_name": pc.product.name,
                    "product_image": pc.product.img_url,
                    "total_quantity_purchased": pc.total_quantity_bought,
                    "total_quantity_supplied": pc.total_quantity_supplied,
                    "last_transaction_date": pc.last_transaction_date
                }
                for pc in all_products_query
            ]
        }), 200

    except NotFound as err:
        current_app.logger.error(f"Company of id: {company_id} not found in {all_company_products.__name__}: {str(err.description)}")
        return jsonify(error=err.description), 404

    except Exception as e:
        current_app.logger.error(f"Error in {all_company_products.__name__}: {str(e)}")
        return jsonify(error="Internal server error"), 500


@analytics_bp.route("/companies/<company_id>/top-products", methods=["GET"])
@requires_auth
def top_10_company_products(company_id):
    """
    Retrieves the top 10 most purchased and most supplied products for a specific company.

    Queries the ProductCompany table, filters by the given company_id, and
    returns the top 10 products ordered by total quantity purchased and total quantity supplied.

    Returns a JSON response containing company information and product details,
    including product ID, name, image URL, and quantities.
    """

    try:
        company = get_user_item_or_404(Company, company_id)

        purchase_query = fetch_product_history(company_id)

        supply_query = fetch_product_history(company_id)

        top_products_supplied = (
            supply_query
            .filter(ProductCompany.total_quantity_supplied > 0)
            .order_by(ProductCompany.total_quantity_supplied.desc())
            .limit(10)
            .all()
        )

        top_products_purchased = (
            purchase_query
            .filter(ProductCompany.total_quantity_bought > 0)
            .order_by(ProductCompany.total_quantity_bought.desc())
            .limit(10)
            .all()
        )

        return jsonify(
            {"company": {
                "id": company.id,
                "name": company.name,
            },
            "top_10_products_purchased" : [
                {
                    "product_id" : p.product.id,
                    "product_name" : p.product.name,
                    "product_image" : p.product.img_url,
                    "total_quantity_purchased" : p.total_quantity_bought
                 }
                for p in top_products_purchased
            ],
            "top_10_products_supplied" : [
                {
                    "product_id": p.product.id,
                    "product_name": p.product.name,
                    "product_image": p.product.img_url,
                    "total_quantity_supplied": p.total_quantity_supplied
                }
                for p in top_products_supplied
            ]
            }
        )


    except NotFound as err:
        current_app.logger.error(f"Company of id: {company_id} not found in {top_10_company_products.__name__}: {str(err.description)}")
        return jsonify(error=err.description), 404

    except Exception as e:
        current_app.logger.error(f"Error in {top_10_company_products.__name__}: {str(e)}")
        return jsonify(error="Internal server error"), 500


@analytics_bp.route("/companies/<company_id>/products/<product_id>", methods=["GET"])
@requires_auth
def product_history(company_id, product_id):
    """
    Retrieves the transaction history for a specific product within a specific company.

    Filters Entry records by the provided company_id and product_id, and eagerly loads
    associated LineItem records. The results are returned in chronological order.

    Returns a JSON object containing company and product metadata, along with a
    list of transactions showing the date, transaction type, document number, and line items.
    Returns average quantities and average transaction values per supply/purchase.

    """

    try:
        # Validate the id's of the product and company provided in the URl
        company = get_user_item_or_404(Company, company_id)
        product = get_user_item_or_404(Product, product_id)

        # Retrieve the relevant entries related to this company and product
        entries = query_results(company_id = company.id, product_id = product.id)

        # Grab the single ProductCompany row
        pc = (
            db.session.query(ProductCompany)
            .filter_by(company_id=company.id, product_id=product.id)
            .one_or_none()
        )
        if not pc:
            raise NotFound(description="No transaction data for this product & company")

        # Even though this helper has been designed to accept multiple PC rows in mind, it can handle this case
        # of a singular connection (One Product - One Company) wrapped into a list without a TypeError
        stats = calculate_transaction_stats(entries = entries, pcs = [ pc ], product_id = product.id)

        # transactions_count = count_transactions(entries_list = entries)
        # purchase_count = transactions_count["purchase"]
        # supply_count = transactions_count["supply"]
        #
        # # Compute total monetary value for each transaction type
        # monetary_totals = sum_monetary_totals(entries_list = entries, product_id = product.id)
        # total_purchase_value = monetary_totals["purchase"]
        # total_supply_value = monetary_totals["supply"]
        #
        # # Calculate averages
        # average_purchase_quantity = round(pc.total_quantity_bought / purchase_count, 2) if purchase_count else 0
        # average_supply_quantity = round(pc.total_quantity_supplied / supply_count, 2) if supply_count else 0
        # average_supply_value = round(total_supply_value / supply_count, 2) if supply_count else 0
        # average_purchase_value = round(total_purchase_value / purchase_count, 2) if purchase_count else 0

        # Return the timeline along with average transaction value
        return jsonify(
            {"company": {
                "id": company.id,
                "name": company.name,
            },
            "product" : {
                "id": product.id,
                "name" : product.name
            },
            "stats" : stats, #{
            #     "totals": {
            #         "quantitative": {
            #             "purchased": pc.total_quantity_bought,
            #             "supplied": pc.total_quantity_supplied
            #         },
            #         "monetary": {
            #             "purchased": total_purchase_value,
            #             "supplied": total_supply_value
            #         }
            #     },
            #     "average_quantity_per_transaction" : {
            #         "supply": average_supply_quantity,
            #         "purchase": average_purchase_quantity
            #     },
            #     "average_value_per_transaction" : {
            #         "supply": average_supply_value,
            #         "purchase": average_purchase_value
            #     },
            #     "transaction_counts" : {
            #         "supply" : supply_count,
            #         "purchase" : purchase_count,
            #     }
            # },
            "transactions" : [
            # Transform each entry to a format workable for the React frontend timeline
                {
                    "date": entry.date,
                    "transaction_type": entry.transaction_type,
                    "document_nr": entry.document_nr,
                    "line_items": [li.to_dict()
                                   for li in entry.line_items
                                   if li.product_id == product.id
                    ] # Serialize line items
                } for entry in entries
            ]
        }), 200

    except NotFound as err:
        current_app.logger.error(f"Product of id: {product_id} or Company of id: {company_id} not found in {product_history.__name__}: {str(err.description)}")
        return jsonify(error=err.description), 404

    except Exception as e:
        current_app.logger.error(f"Error in product history: {str(e)}")
        return jsonify(error="Internal server error"), 500
