from flask import Blueprint

entries_bp = Blueprint("entries", __name__)

from . import routes