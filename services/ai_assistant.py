from openai import OpenAI
from flask import current_app
from models import db, Sale, SaleItem, Product, Customer, User, Payment, InventoryLog
from sqlalchemy import func
from datetime import datetime, date, timedelta


def _get_client():
    return OpenAI(api_key=current_app.config['OPENAI_API_KEY'])


def _build_store_context():
    """Pull live data from the database and build a rich context string for the AI."""
    today = date.today()
    yesterday = today - timedelta(days=1)
    week_start = today - timedelta(days=7)
    month_start = today - timedelta(days=30)

    # --- Today's stats ---
    today_sales = Sale.query.filter(
        func.date(Sale.created_at) == today,
        Sale.status == 'completed'
    ).all()
    today_revenue = sum(s.total_amount for s in today_sales)
    today_count = len(today_sales)
    today_discount = sum(s.discount for s in today_sales)

    # --- Yesterday's stats ---
    yesterday_sales = Sale.query.filter(
        func.date(Sale.created_at) == yesterday,
        Sale.status == 'completed'
    ).all()
    yesterday_revenue = sum(s.total_amount for s in yesterday_sales)
    yesterday_count = len(yesterday_sales)

    # --- This week ---
    week_sales = Sale.query.filter(
        Sale.created_at >= datetime.combine(week_start, datetime.min.time()),
        Sale.status == 'completed'
    ).all()
    week_revenue = sum(s.total_amount for s in week_sales)
    week_count = len(week_sales)

    # --- This month ---
    month_sales = Sale.query.filter(
        Sale.created_at >= datetime.combine(month_start, datetime.min.time()),
        Sale.status == 'completed'
    ).all()
    month_revenue = sum(s.total_amount for s in month_sales)
    month_count = len(month_sales)

    # --- ALL TIME stats ---
    all_sales = Sale.query.filter_by(status='completed').all()
    all_time_revenue = sum(s.total_amount for s in all_sales)
    all_time_count = len(all_sales)
    first_sale = Sale.query.filter_by(status='completed').order_by(Sale.created_at.asc()).first()
    store_open_date = first_sale.created_at.strftime('%Y-%m-%d') if first_sale else 'N/A'

    # --- Day-by-day breakdown last 7 days (for bar chart) ---
    daily_breakdown = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        d_sales = Sale.query.filter(
            func.date(Sale.created_at) == d,
            Sale.status == 'completed'
        ).all()
        daily_breakdown.append({
            'date': d.strftime('%a %d %b'),
            'count': len(d_sales),
            'revenue': sum(s.total_amount for s in d_sales)
        })

    # --- Top 10 products ALL TIME ---
    top_all_time = db.session.query(
        Product.product_name,
        Product.category,
        func.sum(SaleItem.quantity).label('qty'),
        func.sum(SaleItem.subtotal).label('revenue')
    ).join(SaleItem, SaleItem.product_id == Product.id)\
     .join(Sale, Sale.id == SaleItem.sale_id)\
     .filter(Sale.status == 'completed')\
     .group_by(Product.id)\
     .order_by(func.sum(SaleItem.quantity).desc())\
     .limit(10).all()

    # --- Top 5 products this week ---
    top_products_week = db.session.query(
        Product.product_name,
        func.sum(SaleItem.quantity).label('qty'),
        func.sum(SaleItem.subtotal).label('revenue')
    ).join(SaleItem, SaleItem.product_id == Product.id)\
     .join(Sale, Sale.id == SaleItem.sale_id)\
     .filter(Sale.created_at >= datetime.combine(week_start, datetime.min.time()),
             Sale.status == 'completed')\
     .group_by(Product.id)\
     .order_by(func.sum(SaleItem.quantity).desc())\
     .limit(5).all()

    # --- Products NEVER sold ---
    sold_product_ids = db.session.query(SaleItem.product_id).distinct()
    never_sold = Product.query.filter(~Product.id.in_(sold_product_ids)).all()

    # --- All products with full details ---
    all_products = Product.query.order_by(Product.category, Product.product_name).all()

    # --- Low / critical stock ---
    low_stock = Product.query.filter(Product.quantity <= 15).order_by(Product.quantity).all()
    critical_stock = [p for p in low_stock if p.quantity <= 5]
    out_of_stock = [p for p in all_products if p.quantity == 0]

    # --- Profit analysis per product ---
    total_potential_profit = sum((p.price - p.cost_price) * p.quantity for p in all_products)
    total_cost_stock = sum(p.cost_price * p.quantity for p in all_products)
    total_sell_stock = sum(p.price * p.quantity for p in all_products)

    # --- Actual profit from all-time sales ---
    all_time_profit = db.session.query(
        func.sum((SaleItem.unit_price - Product.cost_price) * SaleItem.quantity)
    ).join(Product, Product.id == SaleItem.product_id)\
     .join(Sale, Sale.id == SaleItem.sale_id)\
     .filter(Sale.status == 'completed').scalar() or 0

    # --- Payment method breakdown (all time + last 30 days) ---
    payment_alltime = db.session.query(
        Sale.payment_method,
        func.count(Sale.id).label('count'),
        func.sum(Sale.total_amount).label('total')
    ).filter(Sale.status == 'completed')\
     .group_by(Sale.payment_method).all()

    payment_month = db.session.query(
        Sale.payment_method,
        func.count(Sale.id).label('count'),
        func.sum(Sale.total_amount).label('total')
    ).filter(
        Sale.created_at >= datetime.combine(month_start, datetime.min.time()),
        Sale.status == 'completed'
    ).group_by(Sale.payment_method).all()

    # --- Cashier performance (all time) ---
    cashier_alltime = db.session.query(
        User.username,
        User.role,
        func.count(Sale.id).label('sales'),
        func.sum(Sale.total_amount).label('revenue')
    ).join(Sale, Sale.user_id == User.id)\
     .filter(Sale.status == 'completed')\
     .group_by(User.id).all()

    # --- Cashier performance this week ---
    cashier_week = db.session.query(
        User.username,
        func.count(Sale.id).label('sales'),
        func.sum(Sale.total_amount).label('revenue')
    ).join(Sale, Sale.user_id == User.id)\
     .filter(Sale.created_at >= datetime.combine(week_start, datetime.min.time()),
             Sale.status == 'completed')\
     .group_by(User.id).all()

    # --- Customer stats ---
    total_customers = Customer.query.count()
    all_customers = Customer.query.order_by(Customer.loyalty_points.desc()).all()
    customers_with_sales = db.session.query(
        Customer.name, Customer.phone, Customer.loyalty_points,
        func.count(Sale.id).label('visits'),
        func.sum(Sale.total_amount).label('spent')
    ).join(Sale, Sale.customer_id == Customer.id)\
     .filter(Sale.status == 'completed')\
     .group_by(Customer.id)\
     .order_by(func.sum(Sale.total_amount).desc()).all()

    # --- Sales trend (compare last 7 days vs previous 7 days) ---
    prev_week_start = week_start - timedelta(days=7)
    prev_week_sales = Sale.query.filter(
        Sale.created_at >= datetime.combine(prev_week_start, datetime.min.time()),
        Sale.created_at < datetime.combine(week_start, datetime.min.time()),
        Sale.status == 'completed'
    ).all()
    prev_week_revenue = sum(s.total_amount for s in prev_week_sales)
    if prev_week_revenue > 0:
        trend_pct = round(((week_revenue - prev_week_revenue) / prev_week_revenue) * 100, 1)
        trend_dir = 'increasing' if trend_pct > 2 else 'declining' if trend_pct < -2 else 'stable'
    else:
        trend_pct = 0
        trend_dir = 'stable'

    # --- Recent 10 transactions ---
    recent_sales = Sale.query.filter_by(status='completed')\
        .order_by(Sale.created_at.desc()).limit(10).all()

    # --- Inventory logs (last 20) ---
    recent_logs = InventoryLog.query.order_by(InventoryLog.created_at.desc()).limit(20).all()

    # --- Users/Staff list ---
    all_users = User.query.all()

    # --- Category breakdown ---
    category_stats = db.session.query(
        Product.category,
        func.count(Product.id).label('products'),
        func.sum(Product.quantity).label('total_stock'),
        func.sum(Product.price * Product.quantity).label('stock_value')
    ).group_by(Product.category).all()

    # ===== BUILD CONTEXT STRING =====
    ctx = f"""
=== LIVE STORE DATA (as of {datetime.now().strftime('%Y-%m-%d %H:%M')}) ===

STORE: Pixxxel Supermarket | Ghana | Currency: Ghana Cedis (₵)
Store opened (first sale recorded): {store_open_date}

═══════════════════════════════════════
SALES PERFORMANCE SUMMARY
═══════════════════════════════════════

TODAY ({today.strftime('%A, %d %B %Y')}):
  Transactions: {today_count}
  Revenue: ₵{today_revenue:,.2f}
  Discounts given: ₵{today_discount:,.2f}

YESTERDAY ({yesterday.strftime('%A, %d %B %Y')}):
  Transactions: {yesterday_count}
  Revenue: ₵{yesterday_revenue:,.2f}
  Day-over-day change: {'▲' if today_revenue >= yesterday_revenue else '▼'} ₵{abs(today_revenue - yesterday_revenue):,.2f} ({round(((today_revenue - yesterday_revenue) / yesterday_revenue * 100) if yesterday_revenue > 0 else 0, 1):+.1f}%)

THIS WEEK (last 7 days):
  Transactions: {week_count}
  Revenue: ₵{week_revenue:,.2f}
  Trend vs previous week: {trend_dir} ({'+' if trend_pct >= 0 else ''}{trend_pct}%)

THIS MONTH (last 30 days):
  Transactions: {month_count}
  Revenue: ₵{month_revenue:,.2f}

ALL TIME (since {store_open_date}):
  Total transactions: {all_time_count}
  Total revenue: ₵{all_time_revenue:,.2f}
  Total profit earned: ₵{all_time_profit:,.2f}

DAILY SALES CHART DATA (last 7 days - this is what the bar graph shows):
"""
    for d in daily_breakdown:
        bar = '█' * min(int(d['revenue'] / 50), 20)
        ctx += f"  {d['date']}: {d['count']} sales | ₵{d['revenue']:,.2f} {bar}\n"

    ctx += f"""
═══════════════════════════════════════
COMPLETE PRODUCT CATALOGUE & INVENTORY
═══════════════════════════════════════
(Format: Product Name | Category | Selling Price | Cost Price | Profit Margin | Stock Qty | Supplier)
"""
    for p in all_products:
        margin = round(((p.price - p.cost_price) / p.price) * 100, 1) if p.price > 0 else 0
        profit_per_unit = round(p.price - p.cost_price, 2)
        stock_status = 'OUT OF STOCK' if p.quantity == 0 else 'CRITICAL' if p.quantity <= 5 else 'LOW' if p.quantity <= 15 else 'OK'
        ctx += f"  [{stock_status}] {p.product_name} | {p.category} | Sell: ₵{p.price} | Cost: ₵{p.cost_price} | Margin: {margin}% (₵{profit_per_unit}/unit) | Stock: {p.quantity} | {p.supplier or 'N/A'}\n"

    ctx += f"""
INVENTORY SUMMARY:
  Total unique products: {len(all_products)}
  Total units in stock: {sum(p.quantity for p in all_products):,}
  Stock value at cost: ₵{total_cost_stock:,.2f}
  Stock value at selling price: ₵{total_sell_stock:,.2f}
  Potential profit from current stock: ₵{total_potential_profit:,.2f}

STOCK ALERTS:
  Out of stock ({len(out_of_stock)}): {', '.join(p.product_name for p in out_of_stock) if out_of_stock else 'None'}
  Critical (≤5 units) ({len(critical_stock)}): {', '.join(f"{p.product_name} ({p.quantity})" for p in critical_stock) if critical_stock else 'None'}
  Low (≤15 units) ({len(low_stock)}): {', '.join(f"{p.product_name} ({p.quantity})" for p in low_stock) if low_stock else 'None'}

PRODUCT CATEGORIES:
"""
    for cat in category_stats:
        ctx += f"  {cat.category}: {cat.products} products, {cat.total_stock} units, ₵{cat.stock_value:,.2f} value\n"

    ctx += f"""
PRODUCTS NEVER SOLD: {', '.join(p.product_name for p in never_sold) if never_sold else 'All products have been sold at least once'}

═══════════════════════════════════════
TOP SELLING PRODUCTS
═══════════════════════════════════════

ALL TIME TOP 10:
"""
    for i, p in enumerate(top_all_time, 1):
        ctx += f"  {i}. {p.product_name} ({p.category}): {p.qty} units sold | ₵{p.revenue:,.2f} revenue\n"

    ctx += "\nTHIS WEEK TOP 5:\n"
    for i, p in enumerate(top_products_week, 1):
        ctx += f"  {i}. {p.product_name}: {p.qty} units | ₵{p.revenue:,.2f}\n"

    ctx += f"""
═══════════════════════════════════════
PAYMENT METHODS
═══════════════════════════════════════

ALL TIME:
"""
    for pb in payment_alltime:
        ctx += f"  {pb.payment_method.replace('_',' ').title()}: {pb.count} transactions | ₵{pb.total:,.2f}\n"

    ctx += "\nLAST 30 DAYS:\n"
    for pb in payment_month:
        ctx += f"  {pb.payment_method.replace('_',' ').title()}: {pb.count} transactions | ₵{pb.total:,.2f}\n"

    ctx += f"""
═══════════════════════════════════════
STAFF & CASHIER PERFORMANCE
═══════════════════════════════════════

ALL STAFF:
"""
    for u in all_users:
        joined = u.created_at.strftime('%Y-%m-%d') if u.created_at else 'N/A'
        ctx += f"  {u.username} | Role: {u.role} | Active: {u.is_active} | Joined: {joined}\n"

    ctx += "\nCASHIER PERFORMANCE ALL TIME:\n"
    for cp in cashier_alltime:
        ctx += f"  {cp.username} ({cp.role}): {cp.sales} sales | ₵{cp.revenue:,.2f}\n"

    ctx += "\nCASHIER PERFORMANCE THIS WEEK:\n"
    for cp in cashier_week:
        ctx += f"  {cp.username}: {cp.sales} sales | ₵{cp.revenue:,.2f}\n"

    ctx += f"""
═══════════════════════════════════════
CUSTOMERS
═══════════════════════════════════════
Total registered customers: {total_customers}

ALL CUSTOMERS (sorted by loyalty points):
"""
    for c in all_customers:
        joined = c.created_at.strftime('%Y-%m-%d') if c.created_at else 'N/A'
        ctx += f"  {c.name} | Phone: {c.phone or 'N/A'} | Email: {c.email or 'N/A'} | Loyalty: {c.loyalty_points} pts | Joined: {joined}\n"

    ctx += "\nCUSTOMER SPENDING (all time):\n"
    for c in customers_with_sales:
        ctx += f"  {c.name}: {c.visits} visits | Total spent: ₵{c.spent:,.2f} | Loyalty: {c.loyalty_points} pts\n"

    ctx += f"""
═══════════════════════════════════════
RECENT TRANSACTIONS (last 10)
═══════════════════════════════════════
"""
    for s in recent_sales:
        customer_name = s.customer.name if s.customer else 'Walk-in'
        items_summary = ', '.join(f"{si.product.product_name} x{si.quantity}" for si in s.items if si.product) if s.items else 'N/A'
        sale_dt = s.created_at.strftime('%Y-%m-%d %H:%M') if s.created_at else 'N/A'
        ctx += f"  Sale #{s.id} | {sale_dt} | {customer_name} | ₵{s.total_amount} | {(s.payment_method or 'N/A').replace('_',' ').title()} | Items: {items_summary}\n"

    if recent_logs:
        ctx += f"""
═══════════════════════════════════════
RECENT INVENTORY CHANGES (last 20)
═══════════════════════════════════════
"""
        for log in recent_logs:
            log_dt = log.created_at.strftime('%Y-%m-%d %H:%M') if log.created_at else 'N/A'
            product_name = log.product.product_name if log.product else 'Deleted product'
            ctx += f"  {log_dt} | {product_name} | {log.change_type} | Change: {log.quantity_change:+d} | {log.notes or ''}\n"

    return ctx


def get_ai_response(conversation_history: list, user_message: str) -> str:
    client = _get_client()
    store_context = _build_store_context()

    system_prompt = f"""You are PIXA, an intelligent AI business assistant for Pixxxel Supermarket's Point of Sale system in Ghana. You are embedded directly in the POS system and have complete access to all real-time store data.

Your personality: professional, friendly, concise, and actionable. You speak like a smart business analyst who knows the store inside-out.

You can help with:
- Sales analysis: today, yesterday, this week, this month, all time, day-by-day breakdowns
- Profit analysis: per product, per category, overall margins
- Inventory insights: stock levels, restocking recommendations, out-of-stock alerts
- Customer behavior, loyalty analysis, spending patterns
- Cashier performance tracking
- Business recommendations based on data
- Answering questions about how the POS system works and how to navigate it
- Describing what charts/graphs show (you have the underlying data)

POS SYSTEM OVERVIEW:
- Built with Flask (Python), SQLite/PostgreSQL, deployed on Render.com at sales-manager-rb3h.onrender.com
- Modules: Dashboard, Point of Sale (POS), Products, Inventory, Sales History, Customers, Reports
- Payment methods: Cash, MTN Mobile Money (USSD push), Bank Card
- Roles: Admin (full access), Manager (reports + management), Cashier (POS only)
- Loyalty: 1 point per ₵1000 spent, 1% discount per 100 points (max 10%)
- Currency: Ghana Cedis (₵), no VAT/tax applied
- Barcodes on receipts: CODE128 + QR code that links to POS for re-scanning

NAVIGATION GUIDE:
- Dashboard: /dashboard — shows KPIs, sales chart, quick actions
- Point of Sale: /sales/pos — cashier screen to process sales
- Products: /products — add/edit/delete products, barcodes
- Inventory: /inventory — stock levels, restock logs
- Customers: /customers — customer profiles, loyalty points
- Sales History: /sales/history — all past transactions
- Reports: /reports — CSV export, charts, date-range filtering

{store_context}

IMPORTANT RULES:
- Always use ₵ for currency amounts
- Be specific with numbers from the live data above — never guess
- If asked about bar graph / chart data: use the DAILY SALES CHART DATA section above
- If asked about profit: use the cost_price and margin data from the product catalogue
- If asked about all-time stats: use the ALL TIME sections
- Keep responses concise but insightful — use bullet points for lists
- Proactively flag concerns (low stock, declining sales, etc.) when relevant"""

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(conversation_history[-10:])
    messages.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        max_tokens=600,
        temperature=0.7,
    )

    return response.choices[0].message.content
