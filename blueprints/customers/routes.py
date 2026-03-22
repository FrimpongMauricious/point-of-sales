from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Customer, Sale
from blueprints.auth.routes import role_required

customers_bp = Blueprint('customers', __name__, url_prefix='/customers')


@customers_bp.route('/')
@login_required
def list_customers():
    customers = Customer.query.order_by(Customer.name).all()
    return render_template('customers/list.html', customers=customers)


@customers_bp.route('/add', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'manager')
def add_customer():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip() or None
        email = request.form.get('email', '').strip() or None
        address = request.form.get('address', '').strip() or None

        if not name:
            flash('Customer name is required.', 'danger')
            return render_template('customers/add.html')

        if phone and Customer.query.filter_by(phone=phone).first():
            flash('Phone number already exists.', 'danger')
            return render_template('customers/add.html')

        if email and Customer.query.filter_by(email=email).first():
            flash('Email already exists.', 'danger')
            return render_template('customers/add.html')

        customer = Customer(name=name, phone=phone, email=email, address=address)
        db.session.add(customer)
        db.session.commit()
        flash(f'Customer "{name}" added successfully!', 'success')
        return redirect(url_for('customers.list_customers'))

    return render_template('customers/add.html')


@customers_bp.route('/<int:customer_id>')
@login_required
def profile(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    sales = Sale.query.filter_by(customer_id=customer_id).order_by(Sale.created_at.desc()).all()
    return render_template('customers/profile.html', customer=customer, sales=sales)


@customers_bp.route('/edit/<int:customer_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'manager')
def edit_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip() or None
        email = request.form.get('email', '').strip() or None
        address = request.form.get('address', '').strip() or None

        if not name:
            flash('Customer name is required.', 'danger')
            return render_template('customers/edit.html', customer=customer)

        if phone:
            existing = Customer.query.filter_by(phone=phone).filter(Customer.id != customer_id).first()
            if existing:
                flash('Phone number already in use.', 'danger')
                return render_template('customers/edit.html', customer=customer)

        if email:
            existing = Customer.query.filter_by(email=email).filter(Customer.id != customer_id).first()
            if existing:
                flash('Email already in use.', 'danger')
                return render_template('customers/edit.html', customer=customer)

        customer.name = name
        customer.phone = phone
        customer.email = email
        customer.address = address
        db.session.commit()
        flash(f'Customer "{name}" updated.', 'success')
        return redirect(url_for('customers.profile', customer_id=customer_id))

    return render_template('customers/edit.html', customer=customer)


@customers_bp.route('/delete/<int:customer_id>', methods=['POST'])
@login_required
@role_required('admin', 'manager')
def delete_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    name = customer.name
    db.session.delete(customer)
    db.session.commit()
    flash(f'Customer "{name}" deleted.', 'success')
    return redirect(url_for('customers.list_customers'))
