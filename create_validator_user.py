from app import app, db
from models import User, Role

with app.app_context():
    # Create a test user with validator role
    validator_role = Role.query.filter_by(name='validator').first()
    
    if validator_role:
        # Check if the user already exists
        validator_user = User.query.filter_by(username='validator').first()
        
        if not validator_user:
            # Create validator user
            validator_user = User(
                username='validator',
                email='validator@example.com',
                is_active=True,
                role=validator_role
            )
            validator_user.set_password('Validator123!')
            
            try:
                db.session.add(validator_user)
                db.session.commit()
                print('Validator user created successfully')
            except Exception as e:
                db.session.rollback()
                print(f'Error creating validator user: {str(e)}')
        else:
            print('Validator user already exists')
    else:
        print('Validator role not found')