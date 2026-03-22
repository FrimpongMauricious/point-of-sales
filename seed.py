import sys
from app import create_app
from models import db, User, Product, Customer

app = create_app()

with app.app_context():
    # Safety check: never wipe existing data unless --force is passed.
    # This protects sales records across restarts.
    db.create_all()  # create any missing tables (e.g. new columns via fresh DB)

    if User.query.count() > 0 and '--force' not in sys.argv:
        print("Database already has data. Sales records are safe.")
        print("Run with --force to wipe and reseed: python seed.py --force")
        sys.exit(0)

    if '--force' in sys.argv:
        db.drop_all()
        db.create_all()
        print("Forced reseed: all data wiped.")

    # Users
    admin = User(username='admin', email='admin@pixxxel.com', role='admin')
    admin.set_password('admin123')

    manager = User(username='manager', email='manager@pixxxel.com', role='manager')
    manager.set_password('manager123')

    cashier = User(username='cashier', email='cashier@pixxxel.com', role='cashier')
    cashier.set_password('cashier123')

    db.session.add_all([admin, manager, cashier])

    # Products — 5 categories, 22 products
    products = [
        # Beverages
        Product(product_name='Coca-Cola 500ml', category='Beverages', price=1.50, cost_price=0.80, quantity=120, barcode='5000112637922', supplier='Coca-Cola Bottling'),
        Product(product_name='Pepsi 500ml', category='Beverages', price=1.50, cost_price=0.80, quantity=95, barcode='0012000001611', supplier='PepsiCo'),
        Product(product_name='Sprite 500ml', category='Beverages', price=1.50, cost_price=0.80, quantity=80, barcode='5000112637930', supplier='Coca-Cola Bottling'),
        Product(product_name='Water 1.5L', category='Beverages', price=0.80, cost_price=0.30, quantity=200, barcode='5449000000439', supplier='AquaPure'),
        Product(product_name='Orange Juice 1L', category='Beverages', price=2.50, cost_price=1.40, quantity=40, barcode='5000112638158', supplier='Tropicana'),

        # Snacks
        Product(product_name='Lays Classic Chips', category='Snacks', price=1.20, cost_price=0.60, quantity=150, barcode='0028400090612', supplier='Frito-Lay'),
        Product(product_name='Doritos Nacho Cheese', category='Snacks', price=1.50, cost_price=0.75, quantity=100, barcode='0028400090629', supplier='Frito-Lay'),
        Product(product_name='Oreo Cookies', category='Snacks', price=2.00, cost_price=1.10, quantity=60, barcode='0044000032609', supplier='Mondelez'),
        Product(product_name='Pringles Original', category='Snacks', price=2.50, cost_price=1.30, quantity=45, barcode='0038000845024', supplier='Kelloggs'),
        Product(product_name='KitKat Bar', category='Snacks', price=1.00, cost_price=0.50, quantity=12, barcode='7613034626844', supplier='Nestle'),

        # Dairy
        Product(product_name='Full Cream Milk 1L', category='Dairy', price=1.80, cost_price=1.00, quantity=55, barcode='5051790010025', supplier='FarmFresh'),
        Product(product_name='Cheddar Cheese 200g', category='Dairy', price=3.50, cost_price=2.00, quantity=30, barcode='5051790010032', supplier='FarmFresh'),
        Product(product_name='Yogurt Strawberry 500g', category='Dairy', price=2.20, cost_price=1.20, quantity=25, barcode='5051790010049', supplier='Danone'),
        Product(product_name='Butter 250g', category='Dairy', price=2.80, cost_price=1.60, quantity=40, barcode='5051790010056', supplier='Anchor'),

        # Household
        Product(product_name='Dish Soap 500ml', category='Household', price=2.50, cost_price=1.20, quantity=70, barcode='0037000012345', supplier='Procter & Gamble'),
        Product(product_name='Laundry Detergent 1kg', category='Household', price=5.00, cost_price=2.80, quantity=35, barcode='0037000012352', supplier='Unilever'),
        Product(product_name='Toilet Paper 4-Pack', category='Household', price=3.50, cost_price=1.80, quantity=8, barcode='0037000012369', supplier='Charmin'),
        Product(product_name='Hand Sanitizer 250ml', category='Household', price=3.00, cost_price=1.50, quantity=50, barcode='0037000012376', supplier='Dettol'),

        # Personal Care
        Product(product_name='Shampoo 400ml', category='Personal Care', price=4.50, cost_price=2.50, quantity=45, barcode='0302990119006', supplier='Head & Shoulders'),
        Product(product_name='Toothpaste 100ml', category='Personal Care', price=2.00, cost_price=1.00, quantity=60, barcode='0302993040025', supplier='Colgate'),
        Product(product_name='Deodorant Spray', category='Personal Care', price=3.50, cost_price=1.80, quantity=3, barcode='0302993040032', supplier='Dove'),
        Product(product_name='Body Lotion 400ml', category='Personal Care', price=5.00, cost_price=2.80, quantity=20, barcode='0302993040049', supplier='Nivea'),
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
    print("Database seeded successfully!")
    print("   Admin:   admin / admin123")
    print("   Manager: manager / manager123")
    print("   Cashier: cashier / cashier123")
