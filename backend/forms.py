from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, FileField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
import re

def validate_cit_email(form, field):
    pattern = r'^\d{16}@cit\.edu\.in$'
    if not re.match(pattern, field.data):
        raise ValidationError('Email must be in format: 16 digits followed by @cit.edu.in')

def validate_password_matches_email(form, field):
    if hasattr(form, 'email') and form.email.data:
        email_digits = form.email.data[:16]
        if field.data != email_digits:
            raise ValidationError('Password must be the 16 digits from your email')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email(), validate_cit_email])
    password = PasswordField('Password', validators=[DataRequired(), validate_password_matches_email])

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email(), validate_cit_email])
    password = PasswordField('Password', validators=[DataRequired(), validate_password_matches_email])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Role', choices=[('student', 'Student'), ('teacher', 'Teacher')], validators=[DataRequired()])

class UploadForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    subject = StringField('Subject', validators=[DataRequired()])
    description = TextAreaField('Description')
    department = SelectField('Department', coerce=int, validators=[DataRequired()])
    file = FileField('PDF File', validators=[DataRequired()])