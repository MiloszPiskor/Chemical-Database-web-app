# GET /analytics/top-products /analytics/global/summary?start=YYYY-MM-DD%end=YYYY-MM-DD
# GET /analytics/top-companies /analytics/global/top-products?range=month
# GET /analytics/monthly-summary /analytics/global/top-companies?range=month
from datetime import datetime, timedelta
from analytics import analytics_bp
from analytics.utils import get_entry_totals_filtered, parse_date_range, get_companies_tally, get_products_tally, \
    get_month_periods, compare_months, compare_periods
from flask import jsonify, current_app, request
from werkzeug.exceptions import NotFound
from models import Product, Company
from utils import get_user_item_or_404, requires_auth

@analytics_bp.route("/global/summary", methods = ["GET"])
@requires_auth
def global_summary():

    try:

        start_date = request.args.get("start")
        end_date = request.args.get("end")
        product_id = request.args.get("product_id")
        company_id = request.args.get("company_id")

        try:
            product = get_user_item_or_404(Product, int(product_id)) if product_id else None
            company = get_user_item_or_404(Company, int(company_id)) if company_id else None
        except ValueError:
            current_app.logger.error(f"Wrong Product/ Company ID provided by the client in {global_summary.__name__}.")
            return jsonify({"error": f"Invalid Product: '{product_id}' ID or Company: '{company_id}' ID. An integer expected."}), 400

        # Default fallback: last 30 days. Custom errors to keep error catching logic in helper and avoid
        # repeating it in each route.
        try:
            start, end = parse_date_range(start_date, end_date)
        except ValueError as e:
            current_app.logger.error(f"Date parsing error in {global_summary.__name__}: {str(e)}")
            return jsonify({"error": str(e)}), 400

        # REFACTORING FOR SQL AGGREGATION EFFICIENCY

        # filtered_sales = filter_entries_by_date(start = start, end = end)
        #
        # totals = {"supply" : 0, "purchase": 0}
        # for e in filtered_sales:
        #     val = sum(li.quantity * li.price_per_unit for li in e.line_items)
        #     totals[e.transaction_type.lower()] += val
        #
        # return jsonify({
        #     "start_date": start.isoformat(),
        #     "end_date": end.isoformat(),
        #     "totals": totals
        # })

        monetary_totals = get_entry_totals_filtered(start = start, end = end, product = product, company = company)

        # Fallback checking for empty keys if default 'None' returned if no query results somehow failed.
        if not monetary_totals or (monetary_totals["supply"] == 0 and monetary_totals["purchase"] == 0):

            current_app.logger.info(f"Received global summary request with args: {dict(request.args)}."
                                    f"No data fetched for query: start- {start_date if start_date else 'no data'}, end-"
                                    f"{end_date if end_date else 'no data'}. Returning fallback response for no data found.")
            return jsonify({"message": "No supply or purchase data found for the selected filters.",
                            "empty": True,
                            "filters": {
                                "start_date": start.isoformat(),
                                "end_date": end.isoformat(),
                                "product": product.name if product else "",
                                "company": company.name if company else ""
                            }
                            }), 200 # 204 would be more appropriate, but it is not supported by Flask (no response returned then)

        return jsonify({
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "monetary_totals": monetary_totals
        })

    except NotFound as err:

        current_app.logger.error(f"No Product/ Company found for given id's in {global_summary.__name__}: {str(err.description)}")
        return jsonify(error=err.description), 404

    except ValueError as e:

        current_app.logger.error(f"Wrong data format provided by the client in {global_summary.__name__}: {str(e)}")
        return jsonify({"error": str(e)}), 400

    except Exception as e:
        current_app.logger.error(f"Unexpected error in {global_summary.__name__}: {str(e)}")
        return jsonify(error="Internal server error"), 500

@analytics_bp.route("/global/products-tally", methods = ["GET"])
@requires_auth
def global_by_products():

    try:

        start_date = request.args.get("start")
        end_date = request.args.get("end")
        limit = request.args.get("limit")

        if limit:
            try:
                limit = int(limit)
                if limit <= 0:
                    current_app.logger.error(f"Non-positive 'limit' filter input in {global_by_products.__name__}.")
                    return jsonify({"error": f"Invalid input for limit filter: '{limit}'. A positive value (integer) expected."}), 400
            except ValueError:
                current_app.logger.error(f"Invalid 'limit' filter input in {global_by_products.__name__}.")
                return jsonify({"error": f"Invalid input for limit filter: '{limit}'. An integer expected."}), 400

        try:
            if not start_date and not end_date:
                start, end = parse_date_range(start_date, end_date, fallback_days = "all")
            else:
                start, end = parse_date_range(start_date, end_date)
        except ValueError as e:
            current_app.logger.error(f"Date parsing error in {global_by_products.__name__}: {str(e)}")
            return jsonify({"error": str(e)}), 400

        all_products_tally = get_products_tally(start = start, end = end, limit = limit)

        if not all_products_tally or (not all_products_tally.get("supply") and not all_products_tally.get("purchase")):
            current_app.logger.info(f"Received global top-products tally request with args: {dict(request.args)}."
                                    f"No data fetched for query: start- {start_date if start_date else 'no data'}, end-"
                                    f"{end_date if end_date else 'no data'}. Returning fallback response for no data found.")
            return jsonify({"message": "No products supplied or purchased found for the selected time period.",
                            "empty": True,
                            "filters": {
                                "start_date": start.isoformat(),
                                "end_date": end.isoformat(),
                                "limit" : limit if limit else ""
                            }
                            }), 200

        return jsonify({
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "products_monetary_totals": all_products_tally
        })

    except Exception as e:
        current_app.logger.error(f"Unexpected error in {global_by_products.__name__}: {str(e)}")
        return jsonify(error="Internal server error"), 500

@analytics_bp.route("/global/companies-tally", methods = ["GET"])
@requires_auth
def global_by_companies():

    try:

        start_date = request.args.get("start")
        end_date = request.args.get("end")
        limit = request.args.get("limit")

        if limit:
            try:
                limit = int(limit)
                if limit <= 0:
                    current_app.logger.error(f"Non-positive 'limit' filter input in {global_by_companies.__name__}.")
                    return jsonify({"error": f"Invalid input for limit filter: '{limit}'. A positive value (integer) expected."}), 400
            except ValueError:
                current_app.logger.error(f"Invalid 'limit' filter input in {global_by_companies.__name__}.")
                return jsonify({"error": f"Invalid input for limit filter: '{limit}'. An integer expected."}), 400

        try:
            if not start_date and not end_date:
                start, end = parse_date_range(start_date, end_date, fallback_days = "all")
            else:
                start, end = parse_date_range(start_date, end_date)
        except ValueError as e:
            current_app.logger.error(f"Date parsing error in {global_by_companies.__name__}: {str(e)}")
            return jsonify({"error": str(e)}), 400

        all_companies_tally = get_companies_tally(start = start, end = end, limit = limit)

        if not all_companies_tally or (not all_companies_tally.get("supply") and not all_companies_tally.get("purchase")):
            current_app.logger.info(f"Received global top-companies tally request with args: {dict(request.args)}."
                                    f"No data fetched for query: start- {start_date if start_date else 'no data'}, end-"
                                    f"{end_date if end_date else 'no data'}. Returning fallback response for no data found.")
            return jsonify({"message": "No records of supplies or purchases found by any company for the selected time period.",
                            "empty": True,
                            "filters": {
                                "start_date": start.isoformat(),
                                "end_date": end.isoformat(),
                                "limit" : limit if limit else ""
                            }
                            }), 200

        return jsonify({
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "companies_monetary_totals": all_companies_tally
        })

    except Exception as e:
        current_app.logger.error(f"Unexpected error in {global_by_companies.__name__}: {str(e)}")
        return jsonify(error="Internal server error"), 500

@analytics_bp.route("/global/quick-trends", methods = ["GET"])
@requires_auth
def global_quick_trends():

    try:

        try:
            this_month_start, this_month_end = get_month_periods(0)
            last_month_start, last_month_end = get_month_periods(1)
            two_months_back_start, two_months_back_end = get_month_periods(2)
        except ValueError as e:
            return jsonify(error=str(e))

        this_month_summary = get_entry_totals_filtered(start = this_month_start, end = this_month_end, trends = True)
        last_month_summary = get_entry_totals_filtered(start = last_month_start, end = last_month_end, trends = True)
        two_months_back_summary = get_entry_totals_filtered(start = two_months_back_start, end = two_months_back_end, trends = True)

        # Removing the filters key from the monthly totals analysis. They are not used here
        # therefore should not confuse the user.
        summaries = [this_month_summary, last_month_summary, two_months_back_summary]
        for summary in summaries:
            summary.pop("filters", None)

        change_data = compare_months(this_month_data = this_month_summary, last_month_data = last_month_summary,
                                     two_months_back_data = two_months_back_summary)

        return jsonify({
            "current_month" : this_month_summary,
            "last_month" : last_month_summary,
            "two_months_back" : two_months_back_summary,
            "change_percent" : change_data
        })

    except Exception as e:
        current_app.logger.error(f"Unexpected error in {global_quick_trends.__name__}: {str(e)}")
        return jsonify(error="Internal server error"), 500


@analytics_bp.route("/global/compare-periods", methods = ["GET"])
@requires_auth
def global_compare_periods():

    try:

        # Using simple dictionary style access to trigger KeyError if any parameter is missing.
        # This is intended behavior since 'global_quick_trends' already handles quick last few months data comparison.
        # This endpoint serves as a direct, custom period comparative analysis, therefore all dates are required.
        required_dates = ["start1", "end1", "start2", "end2"]
        try:
            start_date_1, end_date_1, start_date_2, end_date_2 = [request.args[param] for param in required_dates]
        except KeyError:
            return jsonify(error="Please provide all required date periods to launch the analysis."), 400

        product_id = request.args.get("product_id")
        company_id = request.args.get("company_id")

        try:
            product = get_user_item_or_404(Product, int(product_id)) if product_id else None
            company = get_user_item_or_404(Company, int(company_id)) if company_id else None
        except ValueError:
            current_app.logger.error(f"Wrong Product/ Company ID provided by the client in {global_compare_periods.__name__}.")
            return jsonify(
                error=f"Invalid Product: '{product_id}' ID or Company: '{company_id}' ID. An integer expected."), 400

        try:
            start_1, end_1 = parse_date_range(start_date_1, end_date_1)
            start_2, end_2 = parse_date_range(start_date_2, end_date_2)
        except ValueError as e:
            current_app.logger.error(f"Date parsing error in {global_compare_periods.__name__}: {str(e)}")
            return jsonify(error=str(e)), 400

        monetary_totals_1 = get_entry_totals_filtered(start = start_1, end = end_1, product = product, company = company, trends = True)
        monetary_totals_2 = get_entry_totals_filtered(start = start_2, end = end_2, product = product, company = company, trends = True)

        change_data = compare_periods(period_1_data = monetary_totals_1, period_2_data = monetary_totals_2)

        return jsonify({
            f"period_1 ({start_1} - {end_1})": monetary_totals_1,
            f"period_2 ({start_2} - {end_2})": monetary_totals_2,
            "change_percent": change_data
        })

    except NotFound as err:

        current_app.logger.error(f"No Product/ Company found for given id's in {global_compare_periods.__name__}: {str(err.description)}")
        return jsonify(error=err.description), 404

    except ValueError as e:

        current_app.logger.error(f"Wrong data format provided by the client in {global_compare_periods.__name__}: {str(e)}")
        return jsonify(error=str(e)), 400

    except Exception as e:
        current_app.logger.error(f"Unexpected error in {global_compare_periods.__name__}: {str(e)}")
        return jsonify(error="Internal server error"), 500



