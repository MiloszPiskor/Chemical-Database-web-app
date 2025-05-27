from analytics import analytics_bp
from analytics.utils import query_results, calculate_transaction_stats
from flask import jsonify, current_app
from werkzeug.exceptions import NotFound
from extensions import db
from models import Product, ProductCompany
from utils import get_user_item_or_404, requires_auth

@analytics_bp.route("/products/<product_id>/top-partners", methods = ["GET"])
@requires_auth
def top_partners(product_id):

    try:

        product = get_user_item_or_404(Product, product_id)

        # For monetary and qualitative stats:

        entries = query_results(product_id = product.id)

        # transactions_count = count_transactions(entries_list = entries)
        # purchase_count = transactions_count["purchase"]
        # supply_count = transactions_count["supply"]
        #
        # # Compute total monetary value for each transaction type
        # monetary_totals = sum_monetary_totals(entries_list=entries, product_id=product.id)
        # total_purchase_value = monetary_totals["purchase"]
        # total_supply_value = monetary_totals["supply"]
        #
        # Grab the single ProductCompany row
        product_company_query = (
        db.session.query(ProductCompany)
        .filter(ProductCompany.product_id == product_id)
        )
        #
        # # Calculate total quantities for this product
        all_product_companies = product_company_query.all()
        # total_quantity_purchased = sum(pc.total_quantity_bought for pc in all_product_companies)
        # total_quantity_supplied = sum(pc.total_quantity_supplied for pc in all_product_companies)
        #
        # # Calculate averages
        # average_purchase_quantity = round(total_quantity_purchased / purchase_count, 2) if purchase_count else 0
        # average_supply_quantity = round(total_quantity_supplied / supply_count, 2) if supply_count else 0
        # average_supply_value = round(total_supply_value / supply_count, 2) if supply_count else 0
        # average_purchase_value = round(total_purchase_value / purchase_count, 2) if purchase_count else 0

        stats = calculate_transaction_stats(entries = entries, pcs = all_product_companies, product_id = product.id)

        # Filtering the entries query-reusing for efficiency
        top_suppliers = (
            product_company_query
            .filter(ProductCompany.total_quantity_supplied > 0)
            .order_by(ProductCompany.total_quantity_supplied.desc())
            .limit(10)
            .all()
        )

        # Filtering the entries query
        top_buyers = (
            product_company_query
            .filter(ProductCompany.total_quantity_bought > 0)
            .order_by(ProductCompany.total_quantity_bought.desc())
            .limit(10)
            .all()
        )

        return jsonify({
            "product": {
                "id": product.id,
                "name": product.name,
            },
             "stats": stats,#{
            #     "totals": {
            #         "quantitative": {
            #             "purchased": total_quantity_purchased,
            #             "supplied": total_quantity_supplied
            #         },
            #         "monetary": {
            #             "purchased": total_purchase_value,
            #             "supplied": total_supply_value
            #         }
            #     },
            #     "average_quantity_per_transaction": {
            #         "supply": average_supply_quantity,
            #         "purchase": average_purchase_quantity
            #     },
            #     "average_value_per_transaction": {
            #         "supply": average_supply_value,
            #         "purchase": average_purchase_value
            #     },
            #     "transaction_counts": {
            #         "supply": supply_count,
            #         "purchase": purchase_count,
            #     }
            # },
            "top_suppliers": [
                {
                    "company_id": s.company_id,
                    "company_name": s.company.name,
                    "total_supplied": s.total_quantity_supplied,
                    "last_transaction" : s.last_transaction_date
                } for s in top_suppliers
            ],
            "top_buyers": [
                {
                    "company_id": b.company_id,
                    "company_name": b.company.name,
                    "total_bought": b.total_quantity_bought,
                    "last_transaction": b.last_transaction_date
                } for b in top_buyers
            ]
        }), 200

    except NotFound as err:
        current_app.logger.error(f"Product of id: {product_id} not found in {top_partners.__name__}: {str(err.description)}")
        return jsonify(error=err.description), 404

    except Exception as e:
        current_app.logger.error(f"Unexpected error in {top_partners.__name__}: {str(e)}")
        return jsonify(error=f"Internal server error"), 500
