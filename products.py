from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, Blueprint, current_app
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required, login_manager
from flask_ckeditor import CKEditor
from datetime import date
from models import User, Product, Company, LineItem, ProductCompany, db
from forms import ProductForm
import os

products_bp = Blueprint("products", __name__)

def product_check(name):
    """A function that checks if a product entered in the Product Form
    already exists in a database, if it does it redirects the User to the
    specific Product page"""
    check_for_product = Product.query.filter_by(name=name).first()
    if check_for_product:
        flash("This product already exists in the database.")
        return redirect(url_for("products.products"))

@products_bp.route("/products")
@login_required
def products():
    return render_template('products.html')

@products_bp.route("/edit-product/<int:product_id>", methods=["GET", "POST"])
@login_required
def edit_product(product_id):

    products = Product.query.all()
    for product in products:
        print(product.name)
    print(product_id)
    current_app.logger.info(f"The product found by id: {product_id}")
    product = db.get_or_404(Product, product_id)
    form = ProductForm(
        name = product.name,
        customs_code = product.customs_code,
        img_url = product.img_url
    )
    if form.validate_on_submit():
        try:
            for key, value in form.data.items():
                setattr(product, key, value)
            db.session.commit()
            flash(f"Successfully implemented changes to the: {product.name}")
            current_app.logger.info(f"Changes implemented for product: {product.id}.")
            return redirect(url_for('products'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error {e} occurred while editing Product", exc_info=True)
            flash(f"An error occurred while implementing changes for: {product.name}. Please try again", "danger")
            return redirect(url_for('products_bp.products'))

    return render_template('add_product.html', form=form, edit=True)

@products_bp.route("/delete-product")
@login_required
def delete_product():

    id = request.args.get('product_id')
    product = Product.query.filter_by(id=id).first()

@products_bp.route("/new-product", methods=["GET", "POST"])
@login_required
def add_product():

    form = ProductForm()
    if form.validate_on_submit():
        product_check(name=form.name.data)
        new_product = Product(
            name = form.name.data,
            customs_code = form.customs_code.data,
            img_url = form.img_url.data,
            stock= 0,
            user = current_user
        )
        try:
            db.session.add(new_product)
            db.session.commit()
            current_app.logger.info(f"New user {new_product.name} added to the database.")
            flash(f"Success! Added a new product: {new_product.name} to the database.")
            return redirect(url_for('products.products'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error {e} occurred while adding new Product.", exc_info=True)
            flash(f"An error occurred while adding: {new_product.name} to the database. Please try again", "danger")
            return redirect(url_for('products.add_product'))

    return render_template('add_product.html', form=form, edit=False)