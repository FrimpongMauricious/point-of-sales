import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'pos-secret-key-change-in-production-2024')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'pos.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True

    # Business Configuration
    STORE_NAME = 'Pixxxel Supermarket'
    CURRENCY_SYMBOL = '₵'
    TAX_RATE = 0.00  # No tax (Ghana retail)
    LOW_STOCK_THRESHOLD = 15
    CRITICAL_STOCK_THRESHOLD = 5
    LOYALTY_POINTS_RATE = 1000  # 1 point per ₵1000 spent
