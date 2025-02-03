from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.fields.choices import SelectField
from wtforms.fields.numeric import FloatField
from wtforms.fields.simple import PasswordField
from wtforms.validators import DataRequired, URL, Email, Length
from flask_ckeditor import CKEditorField

# Entry Form:
class EntryForm(FlaskForm):
    # Entry fields:
    document_nr = StringField("Number of the document", validators=[DataRequired()])
    transaction_type = SelectField(u"Transaction type", choices=[('purchase','Purchase'),('supply','Supply')])
    # Product fields:
    product_name = SelectField(u'Select product', coerce=int, validators=[DataRequired()])
    # Company fields:
    company_name = SelectField(u'Select company', coerce=int, validators=[DataRequired()])
    # LineItem fields:
    quantity= FloatField("Quantity of the product", validators=[DataRequired()])
    price = FloatField("Price per unit", validators=[DataRequired()])

    submit = SubmitField(label="Submit Post")

# Register Form:
class RegisterForm(FlaskForm):
    name = StringField("Name of Your Account", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min = 8, message=" Password must be at least 8 characters long.")])
    submit = SubmitField(label="Register")

# Login Form:
class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min = 8, message=" Password must be at least 8 characters long.")])
    submit = SubmitField(label="Log in")

# Company Form:
class CompanyForm(FlaskForm):
    name = StringField("Company name", validators=[DataRequired()])
    address = StringField("Company address", validators=[DataRequired()])
    contact_person = StringField("Contact person name", validators=[DataRequired()])
    contact_number = StringField("Company contact number", validators=[DataRequired()])
    submit = SubmitField(label="Register Company")

class ProductForm(FlaskForm):
    name = StringField("Product name", validators=[DataRequired()])
    customs_code = StringField("Customs code of the Product", validators=[DataRequired()])
    img_url = StringField("Product image URL", validators=[URL(), DataRequired()])
    submit = SubmitField(label="Register Product")

