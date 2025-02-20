from functools import wraps
import logging
from flask import Flask, request, redirect, url_for, flash, jsonify, session
from flask_ckeditor import CKEditor
from sqlalchemy import inspect
from sqlalchemy.orm import DeclarativeBase
from flask_bootstrap import Bootstrap5
from models import User, Product, Company
from companies import companies_bp
from products import products_bp
from entries import entries_bp
from dotenv import load_dotenv, find_dotenv
from extensions import db
from utils import requires_auth, get_auth0_public_key
import os
import json

from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity

from urllib.parse import quote_plus, urlencode
from authlib.integrations.flask_client import OAuth

# Loading the environment variables
load_dotenv()

# Initialising the app
app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = False
# Registering the blueprints
app.register_blueprint(companies_bp)
app.register_blueprint(products_bp)
app.register_blueprint(entries_bp)

# Logging setup
if not app.debug:
    handler = logging.FileHandler("app.log")
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)

ckeditor = CKEditor(app)
bootstrap = Bootstrap5(app)

app.secret_key = os.getenv('APP_SECRET_KEY')

# Auth0 setup
oauth = OAuth(app)

oauth.register(
    "auth0",
    client_id=os.getenv("AUTH0_CLIENT_ID"),
    client_secret=os.getenv("AUTH0_CLIENT_SECRET"),
    client_kwargs={
        "scope": "openid profile email",
        "audience": os.getenv("AUTH0_AUDIENCE"),
        "prompt": "login"
    },
    server_metadata_url=f'https://{os.getenv("AUTH0_DOMAIN")}/.well-known/openid-configuration'
)

# CREATE DATABASE
class Base(DeclarativeBase):
    pass
# Load database URI from environment variables
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI', 'sqlite:///mydatabase.db')
# Initialize the db with the app
db.init_app(app)

with app.app_context():
    if not inspect(db.engine).has_table("users"):
        app.logger.error("The 'user' table does not exist.")
    else:
        app.logger.info("User table exists and is ready for queries.")

with app.app_context():
    app.logger.info(f"Registered routes: {[rule.rule for rule in app.url_map.iter_rules()]}")

with app.app_context():
    inspector = inspect(db.engine)
    if not inspector.has_table("users"):
        print("No database found, proceeding to instantiate the Model.")
        db.create_all()
    else:
        print("The database exists, no need to initialize the Model.")

#( CHANGED FOR EASIER TESTABILITY AND DIRECT CONTROL OVER ERROR HANDLING IN VIEWS-- MORE SCALABLE ) -> Now each view function raises 404 on it's own
# 404 Error Handler:
# @app.errorhandler(404)
# def resource_not_found(error):
#     """Error handler for 404 - Resource Not Found"""
#     return jsonify(error = error.description or "Resource not found"), 404

@app.route("/login", methods=["GET"])
def login():
    auth0_login_url = oauth.auth0.authorize_redirect(
        redirect_uri=url_for("callback", _external=True),
        audience=os.getenv("AUTH0_AUDIENCE"),
        scope="openid profile email",
    ).location
    print(url_for("callback", _external=True))
    print("AUTH0_AUDIENCE:", os.getenv("AUTH0_AUDIENCE"))

    return jsonify({"login_url": auth0_login_url}), 200

@app.route("/callback", methods=["GET", "POST"])
def callback():
    token = oauth.auth0.authorize_access_token()
    print("Token Audience:", token.get("aud", "MISSING_AUD"))

    print("TOKEN RECEIVED:", json.dumps(token, indent=2))  # Debugging
    print("AUTH0_AUDIENCE from ENV:", os.getenv("AUTH0_AUDIENCE"))
    print("Token Audience:", token.get("aud", "MISSING_AUD"))
    session["user"] = token
    return jsonify({"access_token": token["access_token"]}), 200

@app.route("/protected", methods=["GET"])
@requires_auth
def protected():
    # Print the raw Authorization header (which contains the JWT token)
    # Access specific fields like nickname or email

    print("User Payload:", request.user)
    return jsonify({"message": "You have access!", "user": request.user})


if __name__ == "__main__":
    app.run(debug=True, port=5002)