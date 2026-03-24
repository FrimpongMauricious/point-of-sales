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
        _auto_seed(app)

    return app


def _auto_seed(app):
    """Seed the database on first run if it is empty."""
    from models import User, Product, Customer
    if User.query.count() > 0:
        return  # already seeded

    # Users
    admin = User(username='admin', email='admin@pixxxel.com', role='admin')
    admin.set_password('admin123')
    manager = User(username='manager', email='manager@pixxxel.com', role='manager')
    manager.set_password('manager123')
    cashier = User(username='cashier', email='cashier@pixxxel.com', role='cashier')
    cashier.set_password('cashier123')
    db.session.add_all([admin, manager, cashier])

    # Products
    products = [
        Product(product_name='Coca-Cola 500ml', category='Beverages', price=54.00, cost_price=33.00, quantity=120, barcode='5000112637922', supplier='Coca-Cola Bottling'),
        Product(product_name='Pepsi 500ml', category='Beverages', price=54.00, cost_price=33.00, quantity=95, barcode='0012000001611', supplier='PepsiCo'),
        Product(product_name='Sprite 500ml', category='Beverages', price=54.00, cost_price=33.00, quantity=80, barcode='5000112637930', supplier='Coca-Cola Bottling'),
        Product(product_name='Voltic Water 1.5L', category='Beverages', price=42.00, cost_price=21.00, quantity=200, barcode='5449000000439', supplier='Voltic Ghana'),
        Product(product_name='Minute Maid Orange Juice 1L', category='Beverages', price=168.00, cost_price=102.00, quantity=40, barcode='5000112638158', supplier='Coca-Cola Bottling'),
        Product(product_name='Lays Classic Chips', category='Snacks', price=108.00, cost_price=66.00, quantity=150, barcode='0028400090612', supplier='Frito-Lay'),
        Product(product_name='Doritos Nacho Cheese', category='Snacks', price=132.00, cost_price=81.00, quantity=100, barcode='0028400090629', supplier='Frito-Lay'),
        Product(product_name='Oreo Cookies 137g', category='Snacks', price=150.00, cost_price=90.00, quantity=60, barcode='0044000032609', supplier='Mondelez'),
        Product(product_name='Pringles Original 165g', category='Snacks', price=228.00, cost_price=144.00, quantity=45, barcode='0038000845024', supplier='Kelloggs'),
        Product(product_name='KitKat Bar 45g', category='Snacks', price=90.00, cost_price=54.00, quantity=12, barcode='7613034626844', supplier='Nestle'),
        Product(product_name='Cowbell Full Cream Milk 1L', category='Dairy', price=144.00, cost_price=90.00, quantity=55, barcode='5051790010025', supplier='Promasidor Ghana'),
        Product(product_name='Cheddar Cheese 200g', category='Dairy', price=330.00, cost_price=210.00, quantity=30, barcode='5051790010032', supplier='FarmFresh'),
        Product(product_name='Fan Yogo Strawberry 500ml', category='Dairy', price=168.00, cost_price=102.00, quantity=25, barcode='5051790010049', supplier='Fan Milk Ghana'),
        Product(product_name='Blueband Margarine 250g', category='Dairy', price=132.00, cost_price=84.00, quantity=40, barcode='5051790010056', supplier='Unilever Ghana'),
        Product(product_name='Mama Lemon Dish Soap 500ml', category='Household', price=108.00, cost_price=66.00, quantity=70, barcode='0037000012345', supplier='Lion Chemical'),
        Product(product_name='Omo Laundry Detergent 1kg', category='Household', price=288.00, cost_price=180.00, quantity=35, barcode='0037000012352', supplier='Unilever Ghana'),
        Product(product_name='Toilet Rolls 4-Pack', category='Household', price=180.00, cost_price=108.00, quantity=8, barcode='0037000012369', supplier='Duku Paper'),
        Product(product_name='Dettol Hand Sanitizer 250ml', category='Household', price=192.00, cost_price=114.00, quantity=50, barcode='0037000012376', supplier='Reckitt Ghana'),
        Product(product_name='Head & Shoulders Shampoo 400ml', category='Personal Care', price=270.00, cost_price=168.00, quantity=45, barcode='0302990119006', supplier='P&G Ghana'),
        Product(product_name='Colgate Toothpaste 100ml', category='Personal Care', price=120.00, cost_price=72.00, quantity=60, barcode='0302993040025', supplier='Colgate-Palmolive'),
        Product(product_name='Rexona Deodorant Spray 150ml', category='Personal Care', price=252.00, cost_price=156.00, quantity=3, barcode='0302993040032', supplier='Unilever Ghana'),
        Product(product_name='Nivea Body Lotion 400ml', category='Personal Care', price=330.00, cost_price=204.00, quantity=20, barcode='0302993040049', supplier='Beiersdorf Ghana'),
    ]
    db.session.add_all(products)

    # Customers
    customers = [
        Customer(name='John Mensah', phone='0241234567', email='john.mensah@email.com', address='123 Main St, Accra', loyalty_points=45),
        Customer(name='Ama Asante', phone='0551234567', email='ama.asante@email.com', address='456 Ring Rd, Kumasi', loyalty_points=120),
        Customer(name='Kweku Boateng', phone='0271234567', email='kweku.boateng@email.com', address='789 High St, Takoradi', loyalty_points=30),
        Customer(name='Abena Osei', phone='0201234567', email='abena.osei@email.com', address='321 Accra Mall, Accra', loyalty_points=200),
        Customer(name='Kofi Agyemang', phone='0591234567', email='kofi.agyemang@email.com', address='654 Ring Rd, Kumasi', loyalty_points=75),
    ]
    db.session.add_all(customers)
    db.session.commit()


app = create_app()

if __name__ == '__main__':
    app.run(debug=os.environ.get('FLASK_DEBUG', 'false').lower() == 'true')
