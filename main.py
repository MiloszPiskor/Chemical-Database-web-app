import logging
from flask import Flask, request, url_for,jsonify, session
from flask_migrate import Migrate
from extensions import db
from sqlalchemy import inspect
from dotenv import load_dotenv
import os
import json
from authlib.integrations.flask_client import OAuth
from companies import companies_bp
from products import products_bp
from entries import entries_bp
from utils import requires_auth

# Loading the environment variables
load_dotenv()

# Initialising the app
app = Flask(__name__)
# Load database URI from environment variables
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI', "postgresql://userisme:password123@db:5432/chemical-db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize Flask-Migrate
migrate = Migrate(app, db)

# Initialize the db with the app
db.init_app(app)

with app.app_context():
    inspector = inspect(db.engine)
    if not inspector.has_table("users"):
        print("No database found, proceeding to instantiate the Model.")
        db.create_all()
    else:
        print("The database exists, no need to initialize the Model.")

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

with app.app_context():
    if not inspect(db.engine).has_table("users"):
        app.logger.error("The 'user' table does not exist.")
    else:
        app.logger.info("User table exists and is ready for queries.")

with app.app_context():
    app.logger.info(f"Registered routes: {[rule.rule for rule in app.url_map.iter_rules()]}")

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

@app.route('/health')
def health_check():
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)