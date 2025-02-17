from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, Blueprint, current_app
from models import User, Product, Company, LineItem, ProductCompany, db
import os
from flask import request
from sqlalchemy.exc import IntegrityError, SQLAlchemyError


users_bp = Blueprint("users", __name__)

def get_or_create_user_from_token():
    """Analyzes the JWT Token payload and creates a new User in the database if it doesn't exist"""
    # token = request.headers.get('Authorization').split()[1]
    try:
        decoded_token = request.user
        user_sub = decoded_token['sub']

    except KeyError as e:
        current_app.logger.error(f"Missing expected field in token: {str(e)}")
        return jsonify({"error": "Token missing required field"}), 401

    except Exception as e:
        current_app.logger.error(f"An error occurred while decoding the token: {str(e)}")
        return jsonify({"error": "Token decoding error"}), 401

    user = User.query.filter_by(auth0_sub=user_sub).first()
    if not user:
        # If user doesn't exist in DB, create a new one (considering using profile data from Auth0 here)
        try:
            user = User(
                auth0_sub=user_sub,
                name=decoded_token.get('nickname'),
                email=decoded_token.get('email')
            )
            db.session.add(user)
            db.session.commit()
            current_app.logger.info(f"New user created: {user.id}")

        except IntegrityError as e:
            db.session.rollback()
            current_app.logger.error(f"Database Integrity Error while creating a new User: {str(e)}")
            return jsonify({"error": "Database integrity error"}), 500

        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"SQLAlchemy error while creating a new User: {str(e)}")
            return jsonify({"error": "Database error"}), 500

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"An error occurred while creating a new user: {str(e)}")
            return jsonify({"error": "Internal server error"}), 500
    return user