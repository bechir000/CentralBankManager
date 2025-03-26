from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, HiddenField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from models import User

class LoginForm(FlaskForm):
    """Form for user login"""
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    """Form for user registration"""
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    password2 = PasswordField(
        'Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        """Check if username is already taken"""
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        """Check if email is already registered"""
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

class ChangePasswordForm(FlaskForm):
    """Form for changing user password"""
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField(
        'Confirm New Password', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Change Password')

class CreateUserForm(FlaskForm):
    """Form for creating a new user (admin only)"""
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    role = SelectField('Role', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Create User')

    def validate_username(self, username):
        """Check if username is already taken"""
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        """Check if email is already registered"""
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

class UserEditForm(FlaskForm):
    """Form for editing user details (admin only)"""
    id = HiddenField('ID')
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    role = SelectField('Role', coerce=int, validators=[DataRequired()])
    active = BooleanField('Active')
    submit = SubmitField('Update User')

    def validate_username(self, username):
        """Check if username is already taken by another user"""
        user = User.query.filter_by(username=username.data).first()
        if user is not None and str(user.id) != self.id.data:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        """Check if email is already registered to another user"""
        user = User.query.filter_by(email=email.data).first()
        if user is not None and str(user.id) != self.id.data:
            raise ValidationError('Please use a different email address.')

class UploadForm(FlaskForm):
    """Form for uploading XML files"""
    bank_name = StringField('Bank Name', validators=[DataRequired()])
    xml_file = FileField('XML File', validators=[
        FileRequired(),
        FileAllowed(['xml'], 'XML files only!')
    ])
    submit = SubmitField('Upload')