
import os

DATABASE_CONFIGS = {
    'postgresql': {
        'ENGINE': 'postgresql',
        'SQLALCHEMY_DATABASE_URI': os.environ.get('DATABASE_URL'),
        'SQLALCHEMY_ENGINE_OPTIONS': {
            'pool_recycle': 300,
            'pool_pre_ping': True,
        }
    },
    'mysql': {
        'ENGINE': 'mysql+pymysql',
        'SQLALCHEMY_DATABASE_URI': 'mysql+pymysql://user:password@localhost/dbname',
        'SQLALCHEMY_ENGINE_OPTIONS': {
            'pool_recycle': 3600,
            'pool_pre_ping': True,
        }
    },
    'oracle': {
        'ENGINE': 'oracle+cx_oracle',
        'SQLALCHEMY_DATABASE_URI': 'oracle://user:password@localhost:1521/dbname',
        'SQLALCHEMY_ENGINE_OPTIONS': {
            'pool_recycle': 3600,
            'pool_pre_ping': True,
        }
    }
}

# Set the active database configuration
ACTIVE_DB = 'postgresql'  # Change this to switch databases

def get_database_config():
    return DATABASE_CONFIGS[ACTIVE_DB]
