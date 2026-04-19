import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed (production uses real env vars)
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
    login_manager.use_header = False

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    from blueprints.ai.routes import ai_bp
    from blueprints.auth.routes import auth_bp
    from blueprints.dashboard.routes import dashboard_bp
    from blueprints.products.routes import products_bp
    from blueprints.inventory.routes import inventory_bp
    from blueprints.sales.routes import sales_bp
    from blueprints.payments.routes import payments_bp
    from blueprints.customers.routes import customers_bp
    from blueprints.receipts.routes import receipts_bp
    from blueprints.reports.routes import reports_bp

    app.register_blueprint(ai_bp)
    csrf.exempt(ai_bp)
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

    @app.route('/googleaebe13cc2405d838.html')
    def google_site_verification():
        from flask import Response
        return Response('google-site-verification: googleaebe13cc2405d838.html', mimetype='text/html')

    with app.app_context():
        db.create_all()
        _auto_seed(app)

    return app


def _auto_seed(app):
    """Seed the database on first run if it is empty."""
    from datetime import datetime, timedelta
    from models import User, Product, Customer, Sale, SaleItem, Payment
    if User.query.count() > 0:
        return  # already seeded

    # Users
    admin = User(username='admin', email='admin@pixxxel.com', role='admin')
    admin.set_password('admin@pixxxel')
    manager = User(username='manager', email='manager@pixxxel.com', role='manager')
    manager.set_password('manager@pixxxel')
    cashier = User(username='cashier', email='cashier@pixxxel.com', role='cashier')
    cashier.set_password('cashier@pixxxel')
    db.session.add_all([admin, manager, cashier])

    # Products
    products = [
        Product(product_name='Coca-Cola 500ml', category='Beverages', price=9.00, cost_price=5.50, quantity=120, barcode='5000112637922', supplier='Coca-Cola Bottling'),
        Product(product_name='Pepsi 500ml', category='Beverages', price=9.00, cost_price=5.50, quantity=95, barcode='0012000001611', supplier='PepsiCo'),
        Product(product_name='Sprite 500ml', category='Beverages', price=9.00, cost_price=5.50, quantity=80, barcode='5000112637930', supplier='Coca-Cola Bottling'),
        Product(product_name='Voltic Water 1.5L', category='Beverages', price=7.00, cost_price=3.50, quantity=200, barcode='5449000000439', supplier='Voltic Ghana'),
        Product(product_name='Minute Maid Orange Juice 1L', category='Beverages', price=28.00, cost_price=17.00, quantity=40, barcode='5000112638158', supplier='Coca-Cola Bottling'),
        Product(product_name='Lays Classic Chips', category='Snacks', price=18.00, cost_price=11.00, quantity=150, barcode='0028400090612', supplier='Frito-Lay'),
        Product(product_name='Doritos Nacho Cheese', category='Snacks', price=22.00, cost_price=13.50, quantity=100, barcode='0028400090629', supplier='Frito-Lay'),
        Product(product_name='Oreo Cookies 137g', category='Snacks', price=25.00, cost_price=15.00, quantity=60, barcode='0044000032609', supplier='Mondelez'),
        Product(product_name='Pringles Original 165g', category='Snacks', price=38.00, cost_price=24.00, quantity=45, barcode='0038000845024', supplier='Kelloggs'),
        Product(product_name='KitKat Bar 45g', category='Snacks', price=15.00, cost_price=9.00, quantity=12, barcode='7613034626844', supplier='Nestle'),
        Product(product_name='Cowbell Full Cream Milk 1L', category='Dairy', price=24.00, cost_price=15.00, quantity=55, barcode='5051790010025', supplier='Promasidor Ghana'),
        Product(product_name='Cheddar Cheese 200g', category='Dairy', price=55.00, cost_price=35.00, quantity=30, barcode='5051790010032', supplier='FarmFresh'),
        Product(product_name='Fan Yogo Strawberry 500ml', category='Dairy', price=28.00, cost_price=17.00, quantity=25, barcode='5051790010049', supplier='Fan Milk Ghana'),
        Product(product_name='Blueband Margarine 250g', category='Dairy', price=22.00, cost_price=14.00, quantity=40, barcode='5051790010056', supplier='Unilever Ghana'),
        Product(product_name='Mama Lemon Dish Soap 500ml', category='Household', price=18.00, cost_price=11.00, quantity=70, barcode='0037000012345', supplier='Lion Chemical'),
        Product(product_name='Omo Laundry Detergent 1kg', category='Household', price=48.00, cost_price=30.00, quantity=35, barcode='0037000012352', supplier='Unilever Ghana'),
        Product(product_name='Toilet Rolls 4-Pack', category='Household', price=30.00, cost_price=18.00, quantity=8, barcode='0037000012369', supplier='Duku Paper'),
        Product(product_name='Dettol Hand Sanitizer 250ml', category='Household', price=32.00, cost_price=19.00, quantity=50, barcode='0037000012376', supplier='Reckitt Ghana'),
        Product(product_name='Head & Shoulders Shampoo 400ml', category='Personal Care', price=45.00, cost_price=28.00, quantity=45, barcode='0302990119006', supplier='P&G Ghana'),
        Product(product_name='Colgate Toothpaste 100ml', category='Personal Care', price=20.00, cost_price=12.00, quantity=60, barcode='0302993040025', supplier='Colgate-Palmolive'),
        Product(product_name='Rexona Deodorant Spray 150ml', category='Personal Care', price=42.00, cost_price=26.00, quantity=3, barcode='0302993040032', supplier='Unilever Ghana'),
        Product(product_name='Nivea Body Lotion 400ml', category='Personal Care', price=55.00, cost_price=34.00, quantity=20, barcode='0302993040049', supplier='Beiersdorf Ghana'),
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
    db.session.flush()  # get IDs before creating sales

    # Sample sales — 7 days of history so the graph shows data
    cashier_user = User.query.filter_by(role='cashier').first()
    now = datetime.utcnow()
    seed_sales = [
        # day 6 ago  (indices into products list, qty)
        (6, [(0,2),(1,1)],       'cash',          27.00),
        (6, [(5,1),(9,1)],       'mobile_money',  33.00),
        # day 5 ago
        (5, [(3,3),(10,1)],      'cash',          45.00),
        (5, [(6,1),(7,1)],       'mobile_money',  47.00),
        (5, [(13,2)],            'card',           44.00),
        # day 4 ago
        (4, [(0,1),(2,1),(3,1)], 'cash',          25.00),
        (4, [(11,1),(15,1)],     'card',          103.00),
        # day 3 ago
        (3, [(5,2),(8,1)],       'mobile_money',  74.00),
        (3, [(0,3),(1,2)],       'cash',           45.00),
        (3, [(18,1),(19,1)],     'card',           65.00),
        # day 2 ago
        (2, [(4,1),(6,2)],       'mobile_money',  72.00),
        (2, [(10,2),(13,1)],     'cash',           70.00),
        (2, [(7,1),(9,2)],       'card',           55.00),
        # yesterday
        (1, [(0,2),(5,1),(3,1)], 'cash',           43.00),
        (1, [(11,1),(18,1)],     'mobile_money',  100.00),
        (1, [(6,1),(7,1),(8,1)], 'card',           85.00),
        # today
        (0, [(0,1),(1,1),(2,1)], 'cash',           27.00),
        (0, [(4,1),(9,1)],       'mobile_money',   43.00),
    ]

    all_products = products  # already in session
    for days_ago, items_data, method, total in seed_sales:
        sale_dt = now - timedelta(days=days_ago)
        sale = Sale(
            user_id=cashier_user.id,
            total_amount=total, discount=0.0, tax=0.0,
            payment_method=method, status='completed',
            created_at=sale_dt
        )
        db.session.add(sale)
        db.session.flush()
        for prod_idx, qty in items_data:
            p = all_products[prod_idx]
            db.session.add(SaleItem(
                sale_id=sale.id, product_id=p.id,
                quantity=qty, unit_price=p.price,
                subtotal=round(p.price * qty, 2)
            ))
        db.session.add(Payment(
            sale_id=sale.id, amount_paid=total,
            change_due=0.0, payment_method=method
        ))

    db.session.commit()


app = create_app()

if __name__ == '__main__':
    app.run(debug=os.environ.get('FLASK_DEBUG', 'false').lower() == 'true')
