from flask import Blueprint, render_template, abort
from flask_login import login_required
from models import Sale

receipts_bp = Blueprint('receipts', __name__, url_prefix='/receipts')


@receipts_bp.route('/<int:sale_id>')
@login_required
def receipt(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    return render_template('receipts/receipt.html', sale=sale)
