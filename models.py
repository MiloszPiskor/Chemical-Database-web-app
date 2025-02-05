from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer,Float, String, Text, ForeignKey, inspect, Enum
from werkzeug.security import generate_password_hash, check_password_hash



class Base(DeclarativeBase):
    pass
# Initialize SQLAlchemy
db = SQLAlchemy(model_class=Base)

class User(db.Model,UserMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    email: Mapped[str] = mapped_column(String(250), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(100))

    # Hashed password management:
    def set_password(self, password):
        self.password_hash= generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)

    def check_password(self, password):
        return check_password_hash(password=password, pwhash=self.password_hash)


    # User relationships with the DB Models, All One to Many (Parent)
    entries: Mapped[list["Entry"]] = relationship("Entry", back_populates="user")
    products: Mapped[list["Product"]] = relationship("Product", back_populates="user")
    companies: Mapped[list["Company"]] = relationship("Company", back_populates="user")



class Entry(db.Model):
    __tablename__ = "entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[str] = mapped_column(String(250), nullable=False)
    document_nr: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    transaction_type: Mapped[str] = mapped_column(Enum("Supply", "Purchase", name="transaction_type_enum"), nullable=False)
    REQUIRED_FIELDS = ["date", "document_nr", "transaction_type", "company"]
    TRANSACTION_TYPES = ["Purchase", "Supply"]

    # Relationship of Many to Many with Product through LineItem Model, here the Parent for LineItem
    line_items: Mapped[list["LineItem"]] = relationship("LineItem", back_populates="entry")

    # Relationship of Many to One with Company (CHILD)
    company_id : Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"))
    company: Mapped["Company"] = relationship("Company", back_populates="entries")

    # Relationship of Many to One with user, here the Child for the User
    user_id : Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    user: Mapped["User"] = relationship("User", back_populates="entries")

class Product(db.Model):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    stock: Mapped[float] = mapped_column(Float, nullable=False)
    customs_code: Mapped[str] = mapped_column(String(250), nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)

    # Relationship of Many to Many with Company through ProductCompany Model, here the Parent for ProductCompany
    product_companies: Mapped[list["ProductCompany"]] = relationship("ProductCompany", back_populates="product")

    # Relationship of Many to Many with Entry through LineItem Model, here the Parent for LineItem
    line_items: Mapped[list["LineItem"]] = relationship("LineItem", back_populates="product")

    # Relationship of Many to One with user, here the Child for the User
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    user: Mapped["User"] = relationship("User", back_populates="products")

    def editable_fields(self):
        """Returns a dictionary of fields that are editable by the user."""
        return {
            "name": self.name,
            "customs_code": self.customs_code,
            "img_url": self.img_url
        }

    def to_dict(self):
        """Returns all fields, including the non-editable ones."""
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}

class Company(db.Model):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    address: Mapped[str] = mapped_column(String(250), nullable=False)
    contact_person: Mapped[str] = mapped_column(String(250), nullable=True)
    contact_number: Mapped[str] = mapped_column(String(20), nullable=False)

    # Relationship of One to Many with Entry (PARENT)
    entries: Mapped[list["Entry"]] = relationship("Entry", back_populates="company")

    # Relationship of Many to Many with Product through ProductCompany Model, here the Parent for ProductCompany
    product_companies: Mapped[list["ProductCompany"]] = relationship("ProductCompany", back_populates="company")

    # Relationship of Many to One with user, here the Child for the User
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    user: Mapped["User"] = relationship("User", back_populates="companies")

    def to_dict(self):
        """Returns all fields, including the non-editable ones."""
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}

    @classmethod
    def editable_fields(self):
        """Returns a dictionary of fields that are editable by the user."""
        return {
            "name": self.name,
            "address": self.address,
            "contact_person": self.contact_person,
            "contact_number": self.contact_number,
        }

class ProductCompany(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    total_quantity_bought: Mapped[float] = mapped_column(Float, nullable=False)
    total_quantity_supplied: Mapped[float] = mapped_column(Float, nullable=False)
    last_transaction_date: Mapped[str] = mapped_column(String(250), nullable=False)

    # A relationship of One to Many with Product, here the Child for Product
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"))
    product: Mapped["Product"] = relationship("Product", back_populates="product_companies")

    # A relationship of One to Many with Company, here the Child for Company
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"))
    company: Mapped["Company"] = relationship("Company", back_populates="product_companies")

class LineItem(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    price_per_unit: Mapped[float] = mapped_column(Float, nullable=False)
    REQUIRED_FIELDS = ["quantity", "price_per_unit", "product"]

    # A relationship of One to Many with the Entry, here the Child of Entry
    entry_id: Mapped[int] = mapped_column(Integer, ForeignKey("entries.id"))
    entry: Mapped["Entry"] = relationship("Entry", back_populates="line_items")

    # A relationship of One to Many with the Product, here the Child of Product
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"))
    product: Mapped["Product"] = relationship("Product", back_populates="line_items")


