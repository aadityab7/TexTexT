# TexText/config.py

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # General Flask Config
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(12)
    DEBUG = False
    TESTING = False
    
    # Database Config
    DB_NAME = os.environ.get('DB_NAME') or 'your_db_name'
    DB_USER = os.environ.get('DB_USER') or 'your_db_user'
    DB_PASSWORD = os.environ.get('DB_PASSWORD') or 'your_db_password'
    DB_HOST = os.environ.get('DB_HOST') or 'localhost'
    DB_PORT = os.environ.get('DB_PORT') or '5432'

    @property
    def DATABASE_URI(self):
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

class DevelopmentConfig(Config):
    DEBUG = True
    # Development specific configurations go here

    # Database Config
    DB_NAME = os.environ.get('DEVELOPMENT_DB_NAME') or 'textext'
    DB_USER = os.environ.get('DEVELOPMENT_DB_USER') or 'postgres'
    DB_PASSWORD = os.environ.get('DEVELOPMENT_DB_PASSWORD') or None
    DB_HOST = os.environ.get('DEVELOPMENT_DB_HOST') or 'localhost'
    DB_PORT = os.environ.get('DEVELOPMENT_DB_PORT') or '5432' 

class TestingConfig(Config):
    TESTING = True
    # Testing specific configurations go here

class ProductionConfig(Config):
    # Production specific configurations go here
    pass