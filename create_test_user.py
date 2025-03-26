from app import app, db
from models import User, Role

with app.app_context():
    # Create a test user with uploader role
    uploader_role = Role.query.filter_by(name='uploader').first()
    
    if uploader_role:
        # Check if the user already exists
        test_user = User.query.filter_by(username='user').first()
        
        if not test_user:
            # Create uploader user
            test_user = User(
                username='user',
                email='user@example.com',
                is_active=True,
                role=uploader_role
            )
            test_user.set_password('User123!')
            
            try:
                db.session.add(test_user)
                db.session.commit()
                print('Test user created successfully')
            except Exception as e:
                db.session.rollback()
                print(f'Error creating test user: {str(e)}')
        else:
            print('Test user already exists')
    else:
        print('Uploader role not found')