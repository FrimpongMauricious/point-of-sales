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
        # Beverages (GHS — typical Accra supermarket prices)
        Product(product_name='Coca-Cola 500ml', category='Beverages', price=54.00, cost_price=33.00, quantity=120, barcode='5000112637922', supplier='Coca-Cola Bottling'),
        Product(product_name='Pepsi 500ml', category='Beverages', price=54.00, cost_price=33.00, quantity=95, barcode='0012000001611', supplier='PepsiCo'),
        Product(product_name='Sprite 500ml', category='Beverages', price=54.00, cost_price=33.00, quantity=80, barcode='5000112637930', supplier='Coca-Cola Bottling'),
        Product(product_name='Voltic Water 1.5L', category='Beverages', price=42.00, cost_price=21.00, quantity=200, barcode='5449000000439', supplier='Voltic Ghana'),
        Product(product_name='Minute Maid Orange Juice 1L', category='Beverages', price=168.00, cost_price=102.00, quantity=40, barcode='5000112638158', supplier='Coca-Cola Bottling'),

        # Snacks
        Product(product_name='Lays Classic Chips', category='Snacks', price=108.00, cost_price=66.00, quantity=150, barcode='0028400090612', supplier='Frito-Lay'),
        Product(product_name='Doritos Nacho Cheese', category='Snacks', price=132.00, cost_price=81.00, quantity=100, barcode='0028400090629', supplier='Frito-Lay'),
        Product(product_name='Oreo Cookies 137g', category='Snacks', price=150.00, cost_price=90.00, quantity=60, barcode='0044000032609', supplier='Mondelez'),
        Product(product_name='Pringles Original 165g', category='Snacks', price=228.00, cost_price=144.00, quantity=45, barcode='0038000845024', supplier='Kelloggs'),
        Product(product_name='KitKat Bar 45g', category='Snacks', price=90.00, cost_price=54.00, quantity=12, barcode='7613034626844', supplier='Nestle'),

        # Dairy
        Product(product_name='Cowbell Full Cream Milk 1L', category='Dairy', price=144.00, cost_price=90.00, quantity=55, barcode='5051790010025', supplier='Promasidor Ghana'),
        Product(product_name='Cheddar Cheese 200g', category='Dairy', price=330.00, cost_price=210.00, quantity=30, barcode='5051790010032', supplier='FarmFresh'),
        Product(product_name='Fan Yogo Strawberry 500ml', category='Dairy', price=168.00, cost_price=102.00, quantity=25, barcode='5051790010049', supplier='Fan Milk Ghana'),
        Product(product_name='Blueband Margarine 250g', category='Dairy', price=132.00, cost_price=84.00, quantity=40, barcode='5051790010056', supplier='Unilever Ghana'),

        # Household
        Product(product_name='Mama Lemon Dish Soap 500ml', category='Household', price=108.00, cost_price=66.00, quantity=70, barcode='0037000012345', supplier='Lion Chemical'),
        Product(product_name='Omo Laundry Detergent 1kg', category='Household', price=288.00, cost_price=180.00, quantity=35, barcode='0037000012352', supplier='Unilever Ghana'),
        Product(product_name='Toilet Rolls 4-Pack', category='Household', price=180.00, cost_price=108.00, quantity=8, barcode='0037000012369', supplier='Duku Paper'),
        Product(product_name='Dettol Hand Sanitizer 250ml', category='Household', price=192.00, cost_price=114.00, quantity=50, barcode='0037000012376', supplier='Reckitt Ghana'),

        # Personal Care
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
    print("Database seeded successfully!")
    print("   Admin:   admin / admin123")
    print("   Manager: manager / manager123")
    print("   Cashier: cashier / cashier123")
