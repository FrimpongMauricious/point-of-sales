import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'pos-secret-key-change-in-production-2024')
    _db_url = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join(BASE_DIR, 'pos.db'))
    # Render gives 'postgres://' but SQLAlchemy requires 'postgresql://'
    if _db_url.startswith('postgres://'):
        _db_url = _db_url.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_DATABASE_URI = _db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True

    # Business Configuration
    STORE_NAME = 'Pixxxel Supermarket'
    CURRENCY_SYMBOL = '₵'
    TAX_RATE = 0.00  # No tax (Ghana retail)
    LOW_STOCK_THRESHOLD = 15
    CRITICAL_STOCK_THRESHOLD = 5
    LOYALTY_POINTS_RATE = 1000  # 1 point per ₵1000 spent

    APP_URL = os.environ.get('APP_URL', '').rstrip('/')

    # MTN MoMo API
    MOMO_SUBSCRIPTION_KEY = os.environ.get('MOMO_SUBSCRIPTION_KEY', '')
    MOMO_API_USER_ID = os.environ.get('MOMO_API_USER_ID', '')
    MOMO_API_KEY = os.environ.get('MOMO_API_KEY', '')
    MOMO_ENVIRONMENT = os.environ.get('MOMO_ENVIRONMENT', 'sandbox')
