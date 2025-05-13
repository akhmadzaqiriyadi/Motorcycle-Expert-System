import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev_secret_key')
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', 'mysql://user:password@localhost/motorcycle_expert_system'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False