from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Product, InventoryLog
from blueprints.auth.routes import role_required
from datetime import datetime

inventory_bp = Blueprint('inventory', __name__, url_prefix='/inventory')


@inventory_bp.route('/')
@login_required
@role_required('admin', 'manager')
def overview():
    products = Product.query.order_by(Product.product_name).all()
    return render_template('inventory/overview.html', products=products)


@inventory_bp.route('/alerts')
@login_required
@role_required('admin', 'manager')
def alerts():
    low_stock_products = Product.query.filter(Product.quantity <= 15).order_by(Product.quantity).all()
    return render_template('inventory/alerts.html', products=low_stock_products)


@inventory_bp.route('/adjust/<int:product_id>', methods=['POST'])
@login_required
@role_required('admin', 'manager')
def adjust_stock(product_id):
    product = Product.query.get_or_404(product_id)
    adjustment_type = request.form.get('adjustment_type')  # restock or adjustment
    quantity_change = request.form.get('quantity_change', '0').strip()
    notes = request.form.get('notes', '').strip()

    try:
        quantity_change = int(quantity_change)
    except (ValueError, TypeError):
        flash('Invalid quantity value.', 'danger')
        return redirect(url_for('inventory.overview'))

    if adjustment_type == 'adjustment' and quantity_change < 0:
        new_qty = product.quantity + quantity_change
        if new_qty < 0:
            flash('Adjustment would result in negative stock.', 'danger')
            return redirect(url_for('inventory.overview'))

    product.quantity += quantity_change
    product.updated_at = datetime.utcnow()

    log = InventoryLog(
        product_id=product.id,
        change_type=adjustment_type or 'adjustment',
        quantity_change=quantity_change,
        notes=notes or f'Manual {adjustment_type} by {current_user.username}'
    )
    db.session.add(log)
    db.session.commit()

    flash(f'Stock for "{product.product_name}" updated. New quantity: {product.quantity}', 'success')
    return redirect(request.referrer or url_for('inventory.overview'))


@inventory_bp.route('/log')
@login_required
@role_required('admin', 'manager')
def log():
    logs = InventoryLog.query.order_by(InventoryLog.created_at.desc()).limit(200).all()
    return render_template('inventory/log.html', logs=logs)
