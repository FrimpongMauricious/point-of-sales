from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from models import db, Product, Sale, SaleItem, Customer, InventoryLog, Payment
from datetime import datetime

sales_bp = Blueprint('sales', __name__, url_prefix='/sales')


@sales_bp.route('/pos')
@login_required
def pos():
    products = Product.query.filter(Product.quantity > 0).order_by(Product.category, Product.product_name).all()
    customers = Customer.query.order_by(Customer.name).all()
    tax_rate = current_app.config['TAX_RATE']
    return render_template('sales/pos.html', products=products, customers=customers, tax_rate=tax_rate)


@sales_bp.route('/checkout', methods=['POST'])
@login_required
def checkout():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'No data received.'}), 400

    cart_items = data.get('cart', [])
    if not cart_items:
        return jsonify({'success': False, 'message': 'Cart is empty.'}), 400

    customer_id = data.get('customer_id') or None
    walk_in_phone = (data.get('walk_in_phone') or '').strip() or None
    payment_method = data.get('payment_method', 'cash')
    discount = float(data.get('discount', 0))
    amount_paid = float(data.get('amount_paid', 0))
    reference_number = data.get('reference_number', '') or None
    tax_rate = current_app.config['TAX_RATE']
    loyalty_rate = current_app.config['LOYALTY_POINTS_RATE']

    # New customer data submitted by cashier on 3rd visit
    new_customer_data = data.get('new_customer_data') or {}

    # Resolve customer from phone if no customer_id given
    auto_created_customer = False
    new_customer_name = None
    if not customer_id and walk_in_phone:
        existing_customer = Customer.query.filter_by(phone=walk_in_phone).first()
        if existing_customer:
            customer_id = existing_customer.id
        else:
            prior_visits = Sale.query.filter_by(walk_in_phone=walk_in_phone).count()
            if prior_visits >= 2:
                # 3rd visit — create with cashier-provided details
                cust_name = (new_customer_data.get('name') or '').strip() or f'Customer ({walk_in_phone})'
                cust_email = (new_customer_data.get('email') or '').strip() or None
                cust_address = (new_customer_data.get('address') or '').strip() or None
                new_customer = Customer(
                    name=cust_name,
                    phone=walk_in_phone,
                    email=cust_email,
                    address=cust_address
                )
                db.session.add(new_customer)
                db.session.flush()
                customer_id = new_customer.id
                auto_created_customer = True
                new_customer_name = cust_name

    # Validate items and calculate totals
    subtotal = 0.0
    validated_items = []

    for item in cart_items:
        product = Product.query.get(item.get('product_id'))
        if not product:
            return jsonify({'success': False, 'message': 'Product not found.'}), 400
        qty = int(item.get('quantity', 1))
        if qty <= 0:
            return jsonify({'success': False, 'message': 'Invalid quantity.'}), 400
        if product.quantity < qty:
            return jsonify({'success': False, 'message': f'Insufficient stock for {product.product_name}.'}), 400
        item_subtotal = round(product.price * qty, 2)
        subtotal += item_subtotal
        validated_items.append({
            'product': product,
            'quantity': qty,
            'unit_price': product.price,
            'subtotal': item_subtotal
        })

    tax_amount = round(subtotal * tax_rate, 2)
    total_amount = round(subtotal - discount + tax_amount, 2)

    if payment_method == 'cash' and amount_paid < total_amount:
        return jsonify({'success': False, 'message': 'Insufficient cash tendered.'}), 400

    change_due = round(amount_paid - total_amount, 2) if payment_method == 'cash' else 0.0

    # Create sale record
    sale = Sale(
        user_id=current_user.id,
        customer_id=int(customer_id) if customer_id else None,
        walk_in_phone=walk_in_phone if not customer_id else None,
        total_amount=total_amount,
        discount=discount,
        tax=tax_amount,
        payment_method=payment_method,
        status='completed'
    )
    db.session.add(sale)
    db.session.flush()

    for vi in validated_items:
        sale_item = SaleItem(
            sale_id=sale.id,
            product_id=vi['product'].id,
            quantity=vi['quantity'],
            unit_price=vi['unit_price'],
            subtotal=vi['subtotal']
        )
        db.session.add(sale_item)

        vi['product'].quantity -= vi['quantity']
        vi['product'].updated_at = datetime.utcnow()

        inv_log = InventoryLog(
            product_id=vi['product'].id,
            change_type='sale',
            quantity_change=-vi['quantity'],
            notes=f'Sale #{sale.id}'
        )
        db.session.add(inv_log)

    # Payment record
    payment = Payment(
        sale_id=sale.id,
        amount_paid=amount_paid,
        change_due=change_due,
        payment_method=payment_method,
        reference_number=reference_number
    )
    db.session.add(payment)

    # Loyalty points for linked customer
    if customer_id:
        customer = Customer.query.get(int(customer_id))
        if customer:
            points_earned = int(total_amount // loyalty_rate)
            customer.loyalty_points += points_earned

    db.session.commit()

    return jsonify({
        'success': True,
        'sale_id': sale.id,
        'change_due': change_due,
        'auto_created_customer': auto_created_customer,
        'new_customer_name': new_customer_name
    })


@sales_bp.route('/api/customer-by-phone')
@login_required
def customer_by_phone():
    phone = request.args.get('phone', '').strip()
    if not phone:
        return jsonify({'found': False})

    customer = Customer.query.filter_by(phone=phone).first()
    if customer:
        return jsonify({
            'found': True,
            'id': customer.id,
            'name': customer.name,
            'loyalty_points': customer.loyalty_points
        })

    # Count walk-in visits with this phone
    visit_count = Sale.query.filter_by(walk_in_phone=phone).count()
    return jsonify({
        'found': False,
        'visit_count': visit_count,
        'visits_until_member': max(0, 2 - visit_count)
    })


@sales_bp.route('/history')
@login_required
def history():
    sales = Sale.query.order_by(Sale.created_at.desc()).all()
    return render_template('sales/history.html', sales=sales)


@sales_bp.route('/api/products/search')
@login_required
def search_products():
    q = request.args.get('q', '').strip()
    barcode = request.args.get('barcode', '').strip()

    if barcode:
        products = Product.query.filter(Product.barcode == barcode, Product.quantity > 0).all()
    elif q:
        products = Product.query.filter(
            (Product.product_name.ilike(f'%{q}%')) | (Product.barcode.ilike(f'%{q}%'))
        ).filter(Product.quantity > 0).all()
    else:
        products = Product.query.filter(Product.quantity > 0).all()

    return jsonify([{
        'id': p.id,
        'product_name': p.product_name,
        'category': p.category,
        'price': p.price,
        'quantity': p.quantity,
        'barcode': p.barcode
    } for p in products])
