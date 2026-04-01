import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = 'cia-retest-secret-key-2024'

    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:1234@localhost/ace_cia_rf'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ✅ MAIL CONFIG (FIXED)
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 465
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True

    MAIL_USERNAME = 'yathishanbu@gmail.com'
    MAIL_PASSWORD = 'wnkzzoyrhgizpsak'
