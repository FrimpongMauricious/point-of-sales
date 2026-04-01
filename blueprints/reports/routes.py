import csv
import io
from flask import Blueprint, render_template, request, jsonify, current_app, Response
from flask_login import login_required
from models import db, Sale, SaleItem, Product, User, Payment
from blueprints.auth.routes import role_required
from datetime import date, datetime, timedelta
from sqlalchemy import func, text

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')


@reports_bp.route('/')
@login_required
@role_required('admin', 'manager')
def index():
    today = date.today()
    start_date = request.args.get('start_date', (today - timedelta(days=30)).isoformat())
    end_date = request.args.get('end_date', today.isoformat())

    try:
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
    except ValueError:
        start_dt = datetime.combine(today - timedelta(days=30), datetime.min.time())
        end_dt = datetime.combine(today, datetime.max.time())

    # Daily sales summary
    today_sales = Sale.query.filter(
        func.date(Sale.created_at) == today,
        Sale.status == 'completed'
    ).all()
    daily_revenue = sum(s.total_amount for s in today_sales)
    daily_count = len(today_sales)

    # Sales over time (last 30 days)
    sales_over_time = db.session.query(
        func.date(Sale.created_at).label('sale_date'),
        func.sum(Sale.total_amount).label('revenue')
    ).filter(
        Sale.created_at >= start_dt,
        Sale.created_at <= end_dt,
        Sale.status == 'completed'
    ).group_by(func.date(Sale.created_at)).order_by(text('sale_date')).all()

    sales_dates = [str(r.sale_date) for r in sales_over_time]
    sales_revenue = [round(r.revenue, 2) for r in sales_over_time]

    # Top selling products
    top_products = db.session.query(
        Product.product_name,
        func.sum(SaleItem.quantity).label('total_qty')
    ).join(SaleItem, SaleItem.product_id == Product.id)\
     .join(Sale, Sale.id == SaleItem.sale_id)\
     .filter(Sale.created_at >= start_dt, Sale.created_at <= end_dt, Sale.status == 'completed')\
     .group_by(Product.id)\
     .order_by(func.sum(SaleItem.quantity).desc())\
     .limit(10).all()

    top_product_names = [r.product_name for r in top_products]
    top_product_qtys = [r.total_qty for r in top_products]

    # Sales by payment method
    payment_breakdown = db.session.query(
        Sale.payment_method,
        func.count(Sale.id).label('count'),
        func.sum(Sale.total_amount).label('total')
    ).filter(
        Sale.created_at >= start_dt,
        Sale.created_at <= end_dt,
        Sale.status == 'completed'
    ).group_by(Sale.payment_method).all()

    payment_labels = [r.payment_method or 'Unknown' for r in payment_breakdown]
    payment_counts = [r.count for r in payment_breakdown]

    # Inventory report
    products = Product.query.order_by(Product.quantity).all()

    # Cashier performance
    cashier_performance = db.session.query(
        User.username,
        func.count(Sale.id).label('sale_count'),
        func.sum(Sale.total_amount).label('total_revenue')
    ).join(Sale, Sale.user_id == User.id)\
     .filter(Sale.created_at >= start_dt, Sale.created_at <= end_dt, Sale.status == 'completed')\
     .group_by(User.id).all()

    # Profit report
    period_sales = Sale.query.filter(
        Sale.created_at >= start_dt,
        Sale.created_at <= end_dt,
        Sale.status == 'completed'
    ).all()

    total_revenue = sum(s.total_amount for s in period_sales)

    cost_query = db.session.query(
        func.sum(SaleItem.quantity * Product.cost_price)
    ).join(Product, Product.id == SaleItem.product_id)\
     .join(Sale, Sale.id == SaleItem.sale_id)\
     .filter(Sale.created_at >= start_dt, Sale.created_at <= end_dt, Sale.status == 'completed')\
     .scalar() or 0

    total_cost = round(cost_query, 2)
    gross_profit = round(total_revenue - total_cost, 2)

    return render_template('reports/index.html',
                           daily_revenue=daily_revenue,
                           daily_count=daily_count,
                           sales_dates=sales_dates,
                           sales_revenue=sales_revenue,
                           top_product_names=top_product_names,
                           top_product_qtys=top_product_qtys,
                           payment_labels=payment_labels,
                           payment_counts=payment_counts,
                           products=products,
                           cashier_performance=cashier_performance,
                           total_revenue=total_revenue,
                           total_cost=total_cost,
                           gross_profit=gross_profit,
                           start_date=start_date,
                           end_date=end_date)


@reports_bp.route('/export/sales')
@login_required
@role_required('admin', 'manager')
def export_sales():
    today = date.today()
    start_date = request.args.get('start_date', (today - timedelta(days=30)).isoformat())
    end_date = request.args.get('end_date', today.isoformat())
    try:
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
    except ValueError:
        start_dt = datetime.combine(today - timedelta(days=30), datetime.min.time())
        end_dt = datetime.combine(today, datetime.max.time())

    sales = Sale.query.filter(
        Sale.created_at >= start_dt,
        Sale.created_at <= end_dt,
        Sale.status == 'completed'
    ).order_by(Sale.created_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Sale ID', 'Date', 'Cashier', 'Customer', 'Payment Method', 'Discount', 'Total Amount'])
    for s in sales:
        writer.writerow([
            s.id,
            s.created_at.strftime('%Y-%m-%d %H:%M'),
            s.cashier.username if s.cashier else '',
            s.customer.name if s.customer else 'Walk-in',
            s.payment_method.replace('_', ' ').title(),
            s.discount,
            s.total_amount
        ])

    output.seek(0)
    filename = f"sales_{start_date}_to_{end_date}.csv"
    return Response(output, mimetype='text/csv',
                    headers={'Content-Disposition': f'attachment; filename={filename}'})


@reports_bp.route('/export/inventory')
@login_required
@role_required('admin', 'manager')
def export_inventory():
    products = Product.query.order_by(Product.category, Product.product_name).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Product ID', 'Name', 'Category', 'Price (₵)', 'Cost Price (₵)', 'Stock', 'Supplier', 'Status'])
    for p in products:
        if p.quantity <= 5:
            status = 'Critical'
        elif p.quantity <= 15:
            status = 'Low'
        else:
            status = 'In Stock'
        writer.writerow([p.id, p.product_name, p.category, p.price, p.cost_price, p.quantity, p.supplier or '', status])

    output.seek(0)
    return Response(output, mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename=inventory_report.csv'})
