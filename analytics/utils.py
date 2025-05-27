from datetime import datetime, timedelta
from collections import OrderedDict

from flask import current_app
from sqlalchemy import func, Date, cast, desc
from sqlalchemy.orm import joinedload
from werkzeug.exceptions import NotFound

from extensions import db
from models import Entry, LineItem, Company, Product
from utils import get_user_item_or_404

def query_results(company_id: int = None, product_id: int = None):

    if company_id is None:

        if product_id is None:
            raise NotFound("Query results need parameters to run.")

        entries = (
            db.session.query(Entry)
            .options(joinedload(Entry.line_items))
            .filter(Entry.line_items.any(LineItem.product_id == product_id))
        )
    else:
        entries = (
            db.session.query(Entry)
            .options(joinedload(Entry.line_items))
            .filter(Entry.company_id == company_id)
        )

        if product_id is not None:
            entries = (
                entries.filter(Entry.line_items.any(LineItem.product_id == product_id))
            )

    return entries

def count_transactions(entries_list):
    """
    Returns a dictionary with counts of 'Supply' and 'Purchase' entries
    for the given company (and optional product).
    """


    # Count supplies and purchases in one query each
    supply_count = entries_list.filter(Entry.transaction_type == "Supply").count()
    purchase_count = entries_list.filter(Entry.transaction_type == "Purchase").count()

    return {"supply": supply_count, "purchase": purchase_count}

def sum_monetary_totals(entries_list, product_id = None):
    """
    Returns a dictionary with total monetary value of 'Supply' and 'Purchase' entries
    for the given company (and optional product).
    """

    total = {"supply": 0.0, "purchase": 0.0}
    for e in entries_list:
        val = sum(li.quantity * li.price_per_unit
                  for li in e.line_items
                  if product_id is None or li.product_id == product_id)
        total[e.transaction_type.lower()] += val

    return total

    # query = (
    #     db.session.query(
    #         Entry.transaction_type,
    #         func.sum(LineItem.quantity * LineItem.price_per_unit).label("total_value")
    #     )
    #     .join(LineItem, Entry.line_items)
    #     .filter(Entry.company_id == company_id)
    # )
    #
    # # Optionally filter by product
    # if product_id is not None:
    #     query = query.filter(LineItem.product_id == product_id)
    #
    # # Group by type (Supply/Purchase)
    # query = query.group_by(Entry.transaction_type)
    #
    # # Execute and map to dict
    # results = query.all()
    # total = {"supply": 0.0, "purchase": 0.0}
    # for transaction_type, value in results:
    #     total[transaction_type.lower()] = float(value) if value else 0.0
    #
    # return total


def calculate_transaction_stats(entries, pcs = None, product_id = None):
    """
    Calculate transaction stats, optionally aggregating from a list of ProductCompany rows (pcs).
    """
    counts = count_transactions(entries)
    totals = sum_monetary_totals(entries, product_id = product_id)

    # Sum quantities across all ProductCompany entries
    total_quantity_purchased = sum(pc.total_quantity_bought for pc in pcs) if pcs else sum(getattr(e, 'total_quantity_bought', 0) for e in entries)
    total_quantity_supplied = sum(pc.total_quantity_supplied for pc in pcs) if pcs else sum(getattr(e, 'total_quantity_supplied', 0) for e in entries)

    average_purchase_quantity = round(total_quantity_purchased / counts["purchase"], 2) if counts["purchase"] else 0
    average_supply_quantity = round(total_quantity_supplied / counts["supply"], 2) if counts["supply"] else 0

    stats = {
        "transaction_counts": counts,
        "totals": {
            "quantitative": {
                "purchase": total_quantity_purchased,
                "supply": total_quantity_supplied,
            },
            "monetary": totals,
        },
        "average_quantity_per_transaction": {
            "purchase": average_purchase_quantity,
            "supply": average_supply_quantity,
        },
        "average_value_per_transaction": {
            "purchase": round(totals["purchase"] / counts["purchase"], 2) if counts["purchase"] else 0,
            "supply": round(totals["supply"] / counts["supply"], 2) if counts["supply"] else 0,
        },
    }

    return stats

def filter_entries(start: datetime = None, end: datetime = None, entries = None, companies: bool = False, products:bool = False):
    """Filters given entries by optional date criteria and applies optional eager loading."""

    if entries is None:
        query = db.session.query(Entry)

        # Dynamically building joinedload options
        options = [joinedload(Entry.line_items)]
        if companies:
            options.append(joinedload(Entry.company))
        if products:
            options.append(joinedload(Entry.line_items).joinedload("product"))

        query = query.options(*options)

        if start and end:
            query = query.filter(Entry.date >= start, Entry.date <= end)

        entries = query.all()

    else:

        if start and end:
            entries = entries.filter(Entry.date >= start, Entry.date <= end).all()
        else:
            entries = entries.all()

    return entries

# def group_by_companies(entries):
#     """Filters given set of entries by the company criteria"""
#
#     top_companies = {
#         "supply" : {},
#         "purchase" : {}
#     }
#
#     for entry in entries:
#
#         total = 0
#
#         total = sum(li.quantity * li.price_per_unit for li in entry.line_items)
#
#         if not top_companies[entry.transaction_type.lower()].get(entry.company.name, None):
#             top_companies[entry.transaction_type.lower()][entry.company.name] = total
#
#         else:
#             top_companies[entry.transaction_type.lower()][entry.company.name] += total

def parse_date_range(start_str: str, end_str: str, fallback_days = 30):
    """
    Parses date strings in 'YYYY-MM-DD' format. Returns a tuple of (start_date, end_date).
    Date fallback is (today - fallback_days, today) if date inputs are missing.
    Raises a ValueError if provided inputs are invalid.
    Returns all available time if fallback_days are "all".
    """
    today = datetime.today().date()
    if fallback_days == "all" and not start_str and not end_str:
        return datetime.min.date(), today
    try:
        start = datetime.strptime(start_str, "%Y-%m-%d").date() if start_str else today - timedelta(days=fallback_days)
        end = datetime.strptime(end_str, "%Y-%m-%d").date() if end_str else today
    except ValueError:
        raise ValueError("Invalid date format. Use YYYY-MM-DD.")
    if start > end:
        raise ValueError("Start date must be earlier than or equal to end date.")

    return start, end

def get_entry_totals_filtered(start: datetime, end: datetime, product = None, company = None, trends:bool = False):
    """
    Returns a dictionary with total value of supply and purchase transactions,
    optionally filtered by date range, product ID, and/or company ID.
    If trends is True, returns a dictionary with zero values for both supply
    and purchase to enable percentage computations, otherwise returns None.
    """

    query = (
        db.session.query(
            Entry.transaction_type,
            func.sum(LineItem.quantity * LineItem.price_per_unit)
        )
        .join(Entry.line_items)
        .group_by(Entry.transaction_type)
    )


    sales_summary = {
        "supply": 0,
        "purchase": 0,
        "filters" : {}
    }

    if product:
        query = query.join(LineItem.product).filter(Product.id == product.id)
        sales_summary["filters"]["product"] = {
            "id": product.id,
            "name": product.name
        }

    if company:
        query = query.filter(Entry.company_id == company.id)
        sales_summary["filters"]["company"] = {
            "id": company.id,
            "name": company.name
        }

    if start and end:
        query = query.filter(
            cast(Entry.date, Date) >= start,
            cast(Entry.date, Date) <= end
        )

    results = query.all()

    empty_results = {"supply": 0, "purchase": 0}

    if not results and not trends:
        return None
    if not results and trends:
        current_app.logger.info(f"No data found for period {start} to {end} for trend analysis, returning zeros.")
        return empty_results

    for transaction_type, total_value in results:
        sales_summary[transaction_type.lower()] += total_value

    return sales_summary

def get_companies_tally(start: datetime = None, end: datetime = None, limit: int = None):
    """
    Uses SQL aggregation to return top companies by total transaction value,
    grouped by transaction type.
    Allows to filter the results by 'limit' filter, restricting the number of query results by
    each transaction type to the desired number.
    Allows to filter the results by the chosen date range.
    """

    total_value = func.sum(LineItem.quantity * LineItem.price_per_unit).label("total_value")
    row_number = func.row_number().over(
        partition_by=Entry.transaction_type,
        order_by=desc(total_value)
    ).label("row_num")

    base_query = (
        db.session.query(
            Entry.transaction_type,
            Company.name.label("company_name"),
            total_value,
            row_number
        )
        .join(Entry.line_items)
        .join(Entry.company)
        .group_by(Entry.transaction_type, Company.name) # Window function already handles grouping using 'partition_by', but we need to aggregate results under specific companies.
    )

    if start and end:
        base_query = base_query.filter(
            cast(Entry.date, Date) >= start,
            cast(Entry.date, Date) <= end
        )

    # Using subquery because filtering on a window function is not possible in the same defining query.
    # row_num column must be computed first, then (mimicking WITH -CTE) can be filtered in outer scope.
    subquery = base_query.subquery()
    final_query = db.session.query(
        subquery.c.transaction_type,
        subquery.c.company_name,
        subquery.c.total_value
    )

    # Apply the limit filter only if limit is provided
    if limit is not None:
        final_query = final_query.filter(subquery.c.row_num <= limit)


    results = final_query.all()

    if not results:
        return None

    # Structure the results
    top_companies = {
        "supply": {},
        "purchase": {}
    }

    for transaction_type, company_name, total_value in results:
        top_companies[transaction_type.lower()][company_name] = total_value

    return top_companies

def get_products_tally(start: datetime = None, end: datetime = None, limit:int = None):
    """
    Uses SQL aggregation to return top products by total transaction value,
    grouped by transaction type.
    Allows to filter the results by 'limit' filter, restricting the number of query results by
    each transaction type to the desired number.
    Allows to filter the results by the chosen date range.
    """

    total_value = func.sum(LineItem.quantity * LineItem.price_per_unit).label("total_value")
    row_number = func.row_number().over(
        partition_by=Entry.transaction_type,
        order_by=desc(total_value)
    ).label("row_num")

    base_query = (
        db.session.query(
            Entry.transaction_type,
            Product.name.label("product_name"),
            total_value,
            row_number
        )
        .join(Entry.line_items)
        .join(LineItem.product)
        .group_by(Entry.transaction_type, Product.name)
    )

    if start and end:
        base_query = base_query.filter(
            cast(Entry.date, Date) >= start,
            cast(Entry.date, Date) <= end
        )

    # Wrap with subquery to filter on row_num
    subquery = base_query.subquery()
    final_query = db.session.query(
        subquery.c.transaction_type,
        subquery.c.product_name,
        subquery.c.total_value
    )

    # Apply the limit filter only if limit is provided
    if limit is not None:
        final_query = final_query.filter(subquery.c.row_num <= limit)

    results = final_query.all()

    if not results:
        return None

    # Structure the results
    top_products = OrderedDict({
        "supply": {},
        "purchase": {}
    })

    for transaction_type, product_name, total_value in results:
        top_products[transaction_type.lower()][product_name] = total_value

    return top_products

# def get_quick_trends():
#
#     pass
#
# def compare_periods(start1, end1, start2, end2, product_id = None, company_id = None):
#
#     pass

def get_month_periods(months_ago: int):
    """
    Function (helper for 'global_quick_trends') that determines the first and last day for a month N months ago.
    It outputs the result as a tuple (start, end) meaning the dates (YYYY-MM-DD) of the first and last day of the month determined by
    'months_ago' input:
    - 0: current month,
    - 1: last month,
    -2: two months back.
    """

    today = datetime.today()
    if months_ago == 0:
        start = today.replace(day=1).strftime("%Y-%m-%d")
        end = today.strftime("%Y-%m-%d")

    elif months_ago == 1:
        start = ((today - timedelta(days = today.day)).replace(day=1)).strftime("%Y-%m-%d")
        end = (today.replace(day=1) - timedelta(days = 1)).strftime("%Y-%m-%d")

    elif months_ago == 2:
        start = ((today.replace(day = 1) - timedelta(days = 32)).replace(day=1)).strftime("%Y-%m-%d")
        end = (((today - timedelta(days = today.day)).replace(day=1)) - timedelta(days = 1)).strftime("%Y-%m-%d")
    else:
        raise ValueError(f"The possible inputs for the function: {get_month_periods.__name__}are: 0- for this month,"
                         f"1- for previous month and 2- for two months back.")

    return start, end

def compute_change_percent(current: float, previous: float):

    if previous == 0:
        return None if current == 0 else 100.0
    return round((current - previous) / previous * 100, 1)

def compare_months(this_month_data: dict, last_month_data: dict, two_months_back_data: dict):


    change_data = {
        "supply": {
            "vs_last_month": compute_change_percent(
                this_month_data.get("supply", 0), last_month_data.get("supply", 0)
            ),
            "vs_two_months_back": compute_change_percent(
                this_month_data.get("supply", 0), two_months_back_data.get("supply", 0)
            )
        },
        "purchase": {
            "vs_last_month": compute_change_percent(
                this_month_data.get("purchase", 0), last_month_data.get("purchase", 0)
            ),
            "vs_two_months_back": compute_change_percent(
                this_month_data.get("purchase", 0), two_months_back_data.get("purchase", 0)
            )
        }
    }
    return change_data

def compare_periods(period_1_data: dict, period_2_data: dict):

    change_data = {
        "purchase": {
            "vs_period_2": compute_change_percent(period_1_data.get("purchase", 0), period_2_data.get("purchase", 0))
        },
        "supply": {
            "vs_period_2": compute_change_percent(period_1_data.get("supply", 0), period_2_data.get("supply", 0))
        }
    }

    return change_data






# def get_best_employees(employees):
#
#     row_number = func.row_number().over(
#         partition_by= employees.department,
#         order_by=desc(employees.salary)
#     ).label("row_number")
#
#     query = db.session.query(
#         employees.department.label("department"),
#         employees.name.label("name"),
#         employees.salary.label("salary"),
#         row_number
#     )
#
#     # Filter on row_number
#     sub_query = query.subquery()
#
#     final_query = db.session.query(
#         sub_query.c.department,
#         sub_query.c.name,
#         sub_query.c.salary,
#     )
#     final_query.filter(sub_query.c.row_number <= 2)
#
#     results = final_query.all()



# def get_entry_totals_filtered(start: datetime, end: datetime, product = None, company = None):
#     """
#     Returns a dictionary with total value of supply and purchase transactions,
#     optionally filtered by date range, product ID, and/or company ID.
#     """
#
#     query = (
#         db.session.query(
#             Entry.transaction_type,
#             func.sum(LineItem.quantity * LineItem.price_per_unit)
#         )
#         .join(Entry.line_items)
#         .group_by(Entry.transaction_type)
#     )
#
#
#     sales_summary = {
#         "supply": 0,
#         "purchase": 0,
#         "filters" : {}
#     }
#
#     if product:
#         query = query.join(LineItem.product).filter(Product.id == product.id)
#         sales_summary["filters"]["product"] = {
#             "id": product.id,
#             "name": product.name
#         }
#
#     if company:
#         query = query.filter(Entry.company_id == company.id)
#         sales_summary["filters"]["company"] = {
#             "id": company.id,
#             "name": company.name
#         }
#
#     if start and end:
#         query = query.filter(
#             cast(Entry.date, Date) >= start,
#             cast(Entry.date, Date) <= end
#         )
#
#     results = query.all()
#
#     if not results:
#         return None
#
#     for transaction_type, total_value in results:
#         sales_summary[transaction_type.lower()] += total_value
#
#     return sales_summary





