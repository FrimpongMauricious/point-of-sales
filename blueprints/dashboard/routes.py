from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from models import db, Product, Sale, Customer
from datetime import date
from sqlalchemy import func
from blueprints.auth.routes import role_required

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')


@dashboard_bp.route('/')
@login_required
def index():
    if current_user.role == 'admin':
        return redirect(url_for('dashboard.admin'))
    elif current_user.role == 'manager':
        return redirect(url_for('dashboard.manager'))
    else:
        return redirect(url_for('sales.pos'))


@dashboard_bp.route('/admin')
@login_required
@role_required('admin')
def admin():
    today = date.today()
    total_products = Product.query.count()
    total_customers = Customer.query.count()
    low_stock = Product.query.filter(Product.quantity <= 15).count()

    today_sales = Sale.query.filter(
        func.date(Sale.created_at) == today,
        Sale.status == 'completed'
    ).all()
    total_sales_today = len(today_sales)
    total_revenue_today = sum(s.total_amount for s in today_sales)

    recent_sales = Sale.query.order_by(Sale.created_at.desc()).limit(5).all()

    return render_template('dashboard/admin.html',
                           total_products=total_products,
                           total_customers=total_customers,
                           low_stock=low_stock,
                           total_sales_today=total_sales_today,
                           total_revenue_today=total_revenue_today,
                           recent_sales=recent_sales)


@dashboard_bp.route('/manager')
@login_required
@role_required('manager')
def manager():
    today = date.today()
    low_stock = Product.query.filter(Product.quantity <= 15).count()

    today_sales = Sale.query.filter(
        func.date(Sale.created_at) == today,
        Sale.status == 'completed'
    ).all()
    total_sales_today = len(today_sales)
    total_revenue_today = sum(s.total_amount for s in today_sales)

    recent_sales = Sale.query.order_by(Sale.created_at.desc()).limit(5).all()

    return render_template('dashboard/manager.html',
                           low_stock=low_stock,
                           total_sales_today=total_sales_today,
                           total_revenue_today=total_revenue_today,
                           recent_sales=recent_sales)


@dashboard_bp.route('/cashier')
@login_required
@role_required('cashier')
def cashier():
    return redirect(url_for('sales.pos'))
