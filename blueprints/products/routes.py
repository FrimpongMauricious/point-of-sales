from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from models import db, Product
from blueprints.auth.routes import role_required
from datetime import datetime

products_bp = Blueprint('products', __name__, url_prefix='/products')

CATEGORIES = ['Beverages', 'Snacks', 'Dairy', 'Household', 'Personal Care',
              'Bakery', 'Meat & Seafood', 'Fruits & Vegetables', 'Frozen Foods', 'Other']


@products_bp.route('/')
@login_required
@role_required('admin', 'manager')
def list_products():
    products = Product.query.order_by(Product.product_name).all()
    return render_template('products/list.html', products=products)


@products_bp.route('/add', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'manager')
def add_product():
    if request.method == 'POST':
        name = request.form.get('product_name', '').strip()
        category = request.form.get('category', '').strip()
        price = request.form.get('price', '').strip()
        cost_price = request.form.get('cost_price', '').strip()
        quantity = request.form.get('quantity', '0').strip()
        barcode = request.form.get('barcode', '').strip() or None
        supplier = request.form.get('supplier', '').strip() or None

        errors = []
        if not name:
            errors.append('Product name is required.')
        if not category:
            errors.append('Category is required.')
        try:
            price = float(price)
            if price <= 0:
                errors.append('Price must be greater than 0.')
        except (ValueError, TypeError):
            errors.append('Valid price is required.')
        try:
            cost_price = float(cost_price)
            if cost_price < 0:
                errors.append('Cost price cannot be negative.')
        except (ValueError, TypeError):
            errors.append('Valid cost price is required.')
        try:
            quantity = int(quantity)
            if quantity < 0:
                errors.append('Quantity cannot be negative.')
        except (ValueError, TypeError):
            errors.append('Valid quantity is required.')

        if barcode:
            existing = Product.query.filter_by(barcode=barcode).first()
            if existing:
                errors.append('Barcode already exists.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('products/add.html', categories=CATEGORIES)

        product = Product(
            product_name=name,
            category=category,
            price=price,
            cost_price=cost_price,
            quantity=quantity,
            barcode=barcode,
            supplier=supplier
        )
        db.session.add(product)
        db.session.commit()
        flash(f'Product "{name}" added successfully!', 'success')
        return redirect(url_for('products.list_products'))

    return render_template('products/add.html', categories=CATEGORIES)


@products_bp.route('/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'manager')
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)

    if request.method == 'POST':
        name = request.form.get('product_name', '').strip()
        category = request.form.get('category', '').strip()
        price = request.form.get('price', '').strip()
        cost_price = request.form.get('cost_price', '').strip()
        quantity = request.form.get('quantity', '0').strip()
        barcode = request.form.get('barcode', '').strip() or None
        supplier = request.form.get('supplier', '').strip() or None

        errors = []
        if not name:
            errors.append('Product name is required.')
        try:
            price = float(price)
        except (ValueError, TypeError):
            errors.append('Valid price is required.')
        try:
            cost_price = float(cost_price)
        except (ValueError, TypeError):
            errors.append('Valid cost price is required.')
        try:
            quantity = int(quantity)
        except (ValueError, TypeError):
            errors.append('Valid quantity is required.')

        if barcode:
            existing = Product.query.filter_by(barcode=barcode).filter(Product.id != product_id).first()
            if existing:
                errors.append('Barcode already in use by another product.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('products/edit.html', product=product, categories=CATEGORIES)

        product.product_name = name
        product.category = category
        product.price = price
        product.cost_price = cost_price
        product.quantity = quantity
        product.barcode = barcode
        product.supplier = supplier
        product.updated_at = datetime.utcnow()
        db.session.commit()
        flash(f'Product "{name}" updated successfully!', 'success')
        return redirect(url_for('products.list_products'))

    return render_template('products/edit.html', product=product, categories=CATEGORIES)


@products_bp.route('/delete/<int:product_id>', methods=['POST'])
@login_required
@role_required('admin', 'manager')
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    name = product.product_name
    db.session.delete(product)
    db.session.commit()
    flash(f'Product "{name}" deleted successfully.', 'success')
    return redirect(url_for('products.list_products'))
