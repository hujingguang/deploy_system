from flask.ext.wtf import Form
from wtforms import StringField,BooleanField,SelectField,TextField,SubmitField,PasswordField,ValidationError
from wtforms.validators import DataRequired,Email,EqualTo

class LoginForm(Form):
     email = StringField('Email', validators=[DataRequired("Please enter your email address."),Email("Please enter your email address.")])
     password = PasswordField('Password', validators=[DataRequired("Please enter a password.")])

