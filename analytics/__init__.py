# Main analytics route file registering them all. Grouped for clarity
# from . import company_routes, product_routes, global_routes
from flask import Blueprint

analytics_bp = Blueprint("analytics", __name__, url_prefix="/analytics")

from . import product_routes
from . import company_routes
from . import global_routes

