from app import app, db
import models
from models import Role, User

with app.app_context():
    print("Dropping all tables...")
    db.drop_all()
    print("Creating all tables...")
    db.create_all()
    print("Database tables recreated successfully!")
    
    # Create default roles
    print("Creating default roles...")
    roles = {
        'admin': 'Administrator with full access to the system',
        'validator': 'User who can validate and approve data',
        'uploader': 'User who can upload XML files but cannot validate them',
        'viewer': 'User who can only view data but cannot modify it'
    }
    
    for role_name, description in roles.items():
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            role = Role(name=role_name, description=description)
            db.session.add(role)
    
    db.session.commit()
    print("Default roles created successfully!")
    
    # Create admin user if no users exist
    if User.query.count() == 0:
        print("Creating admin user...")
        admin_role = Role.query.filter_by(name='admin').first()
        
        if admin_role:
            admin = User(
                username='admin',
                email='admin@example.com',
                is_active=True,
                role=admin_role
            )
            admin.set_password('Admin123!')
            
            db.session.add(admin)
            db.session.commit()
            print("Admin user created successfully!")
    else:
        print("Admin user already exists.")