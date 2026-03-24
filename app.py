import os
from flask import Flask, render_template
from flask_login import LoginManager, current_user
from flask_wtf.csrf import CSRFProtect
from models import db, User
from config import Config

csrf = CSRFProtect()
login_manager = LoginManager()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    from blueprints.auth.routes import auth_bp
    from blueprints.dashboard.routes import dashboard_bp
    from blueprints.products.routes import products_bp
    from blueprints.inventory.routes import inventory_bp
    from blueprints.sales.routes import sales_bp
    from blueprints.payments.routes import payments_bp
    from blueprints.customers.routes import customers_bp
    from blueprints.receipts.routes import receipts_bp
    from blueprints.reports.routes import reports_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(sales_bp)
    app.register_blueprint(payments_bp)
    app.register_blueprint(customers_bp)
    app.register_blueprint(receipts_bp)
    app.register_blueprint(reports_bp)

    # Custom error handlers
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    # Context processors
    @app.context_processor
    def inject_config():
        return {
            'STORE_NAME': app.config['STORE_NAME'],
            'CURRENCY_SYMBOL': app.config['CURRENCY_SYMBOL'],
            'TAX_RATE': app.config['TAX_RATE'],
        }

    # Root redirect
    from flask import redirect, url_for as _url_for
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(_url_for('dashboard.index'))
        return redirect(_url_for('auth.login'))

    @app.route('/login')
    def login_shortcut():
        return redirect(_url_for('auth.login'))

    @app.route('/pos')
    def pos_shortcut():
        return redirect(_url_for('sales.pos'))

    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == '__main__':
    app.run(debug=os.environ.get('FLASK_DEBUG', 'false').lower() == 'true')
