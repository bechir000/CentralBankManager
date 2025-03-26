from datetime import datetime
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash

from app import app, db
from models import User, Role, XMLFile
from forms import (
    LoginForm, RegistrationForm, ChangePasswordForm,
    CreateUserForm, UserEditForm
)

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    # Redirect if user is already authenticated
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    form = LoginForm()
    if form.validate_on_submit():
        # Find the user by username
        user = User.query.filter_by(username=form.username.data).first()
        
        # Check if user exists and password is correct
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'danger')
            return redirect(url_for('login'))
            
        # Check if user is active
        if not user.is_active:
            flash('Your account has been deactivated. Please contact an administrator.', 'danger')
            return redirect(url_for('login'))
            
        # Log in the user and update last login time
        login_user(user, remember=form.remember_me.data)
        user.last_login = datetime.now()
        db.session.commit()
        
        # Redirect to next page or dashboard
        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('index')
        return redirect(next_page)
        
    return render_template('login.html', form=form)

# Logout route
@app.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

# Register route
@app.route('/register', methods=['GET', 'POST'])
def register():
    # Redirect if user is already authenticated
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    form = RegistrationForm()
    if form.validate_on_submit():
        # Create a new user
        viewer_role = Role.query.filter_by(name='viewer').first()
        user = User(
            username=form.username.data,
            email=form.email.data,
            is_active=True,
            role=viewer_role  # New users get 'viewer' role by default
        )
        user.set_password(form.password.data)
        
        try:
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred during registration: {str(e)}', 'danger')
    
    return render_template('register.html', form=form)

# User profile route
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        # Verify current password
        if not current_user.check_password(form.current_password.data):
            flash('Current password is incorrect', 'danger')
            return redirect(url_for('profile'))
            
        # Update password
        current_user.set_password(form.new_password.data)
        db.session.commit()
        flash('Your password has been updated', 'success')
        return redirect(url_for('profile'))
        
    return render_template('profile.html', form=form)

# User management routes (admin only)
@app.route('/users')
@login_required
def users():
    # Check if user is admin
    if not current_user.has_role('admin'):
        flash('You do not have permission to access this page', 'danger')
        return redirect(url_for('index'))
        
    # Get all users
    users = User.query.all()
    
    # Create forms with role choices
    roles = Role.query.all()
    role_choices = [(role.id, role.name) for role in roles]
    
    create_form = CreateUserForm()
    create_form.role.choices = role_choices
    
    edit_form = UserEditForm()
    edit_form.role.choices = role_choices
    
    return render_template('users.html', 
                          users=users, 
                          create_form=create_form, 
                          edit_form=edit_form)

# Create user route (admin only)
@app.route('/users/create', methods=['POST'])
@login_required
def create_user():
    # Check if user is admin
    if not current_user.has_role('admin'):
        flash('You do not have permission to perform this action', 'danger')
        return redirect(url_for('index'))
        
    # Get all roles for form choices
    roles = Role.query.all()
    role_choices = [(role.id, role.name) for role in roles]
    
    form = CreateUserForm()
    form.role.choices = role_choices
    
    if form.validate_on_submit():
        # Get the selected role
        role = Role.query.get(form.role.data)
        
        # Create a new user
        user = User(
            username=form.username.data,
            email=form.email.data,
            is_active=True,
            role=role
        )
        user.set_password(form.password.data)
        
        try:
            db.session.add(user)
            db.session.commit()
            flash(f'User {user.username} created successfully', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'danger')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Error in {field}: {error}', 'danger')
    
    return redirect(url_for('users'))

# Edit user route (admin only)
@app.route('/users/edit', methods=['POST'])
@login_required
def edit_user():
    # Check if user is admin
    if not current_user.has_role('admin'):
        flash('You do not have permission to perform this action', 'danger')
        return redirect(url_for('index'))
        
    # Get all roles for form choices
    roles = Role.query.all()
    role_choices = [(role.id, role.name) for role in roles]
    
    form = UserEditForm()
    form.role.choices = role_choices
    
    if form.validate_on_submit():
        user = User.query.get(form.id.data)
        
        if not user:
            flash('User not found', 'danger')
            return redirect(url_for('users'))
            
        # Update user details
        user.username = form.username.data
        user.email = form.email.data
        user.is_active = form.active.data
        user.role = Role.query.get(form.role.data)
        
        try:
            db.session.commit()
            flash(f'User {user.username} updated successfully', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'danger')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Error in {field}: {error}', 'danger')
    
    return redirect(url_for('users'))

# Delete user route (admin only)
@app.route('/users/delete', methods=['POST'])
@login_required
def delete_user():
    # Check if user is admin
    if not current_user.has_role('admin'):
        flash('You do not have permission to perform this action', 'danger')
        return redirect(url_for('index'))
        
    user_id = request.form.get('id')
    
    if not user_id:
        flash('User ID is required', 'danger')
        return redirect(url_for('users'))
        
    user = User.query.get(user_id)
    
    if not user:
        flash('User not found', 'danger')
        return redirect(url_for('users'))
        
    # Prevent deleting yourself
    if user.id == current_user.id:
        flash('You cannot delete your own account', 'danger')
        return redirect(url_for('users'))
        
    try:
        db.session.delete(user)
        db.session.commit()
        flash(f'User {user.username} deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred: {str(e)}', 'danger')
    
    return redirect(url_for('users'))

# Create first admin user if no users exist
def create_admin_user():
    # Check if any users exist
    if User.query.count() == 0:
        admin_role = Role.query.filter_by(name='admin').first()
        
        if admin_role:
            # Create admin user
            admin = User(
                username='admin',
                email='admin@example.com',
                is_active=True,
                role=admin_role
            )
            admin.set_password('Admin123!')
            
            try:
                db.session.add(admin)
                db.session.commit()
                print('Admin user created successfully')
            except Exception as e:
                db.session.rollback()
                print(f'Error creating admin user: {str(e)}')