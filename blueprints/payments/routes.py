from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required
from models import Payment, Sale
from blueprints.auth.routes import role_required

payments_bp = Blueprint('payments', __name__, url_prefix='/payments')


@payments_bp.route('/')
@login_required
@role_required('admin', 'manager')
def list_payments():
    payments = Payment.query.order_by(Payment.created_at.desc()).all()
    return render_template('payments/list.html', payments=payments)


@payments_bp.route('/<int:payment_id>')
@login_required
def detail(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    return render_template('payments/detail.html', payment=payment)
