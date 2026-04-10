import requests
from flask import current_app


ARKESEL_V2_BASE = 'https://sms.arkesel.com/api/v2'


def send_sms(phone: str, message: str) -> bool:
    """
    Send an SMS via Arkesel v2 API (POST with api-key header).
    phone: recipient number, e.g. '0241234567' or '+233241234567'
    Returns True if sent successfully, False otherwise.
    """
    api_key = current_app.config.get('ARKESEL_API_KEY', '')
    sender_id = current_app.config.get('ARKESEL_SENDER_ID', 'Pixxxel')

    if not api_key:
        current_app.logger.warning('[SMS] ARKESEL_API_KEY not configured — SMS skipped.')
        return False

    # Normalize phone to international format for v2 (+233XXXXXXXXX)
    phone = phone.strip().replace(' ', '').replace('-', '')
    if phone.startswith('0') and len(phone) == 10:
        phone = '+233' + phone[1:]
    elif phone.startswith('233') and len(phone) == 12:
        phone = '+' + phone

    payload = {
        'sender': sender_id,
        'message': message,
        'recipients': [phone],
    }

    try:
        resp = requests.post(
            f'{ARKESEL_V2_BASE}/sms/send',
            json=payload,
            headers={'api-key': api_key},
            timeout=15
        )
        result = resp.json()
        if result.get('status') == 'success':
            balance = result.get('sms_balance', '?')
            current_app.logger.info(f'[SMS] Sent to {phone} | SMS balance remaining: {balance}')
            return True
        else:
            current_app.logger.error(f'[SMS] Failed sending to {phone}: {result}')
            return False
    except Exception as e:
        current_app.logger.error(f'[SMS] Exception: {e}')
        return False


def send_sale_receipt(phone: str, sale_id: int, total: float, payment_method: str,
                      items: list = None, discount: float = 0.0, loyalty_points: int = 0,
                      customer_name: str = None, change_due: float = 0.0,
                      store_name: str = 'Pixxxel Supermarket') -> bool:
    """
    Send a warm receipt SMS to a customer after purchase.
    items: list of dicts with keys: product_name, quantity, unit_price, subtotal
    """
    method_label = {
        'cash': 'Cash',
        'card': 'Card',
        'momo': 'Mobile Money',
        'paystack': 'Mobile Money/Card',
    }.get(payment_method, payment_method.title())

    # Use GHS instead of ₵ symbol — safer for SMS encoding
    currency = 'GHS '

    greeting = f"Hi {customer_name}," if customer_name else "Hello,"
    sep = '-' * 22

    lines = [
        store_name,
        sep,
        greeting,
        "Thank you for shopping with us!",
        sep,
        f"Receipt No: #{sale_id}",
    ]

    # Item breakdown (cap at 4 items to keep SMS concise)
    if items:
        lines.append("Items purchased:")
        for item in items[:4]:
            name = item['product_name']
            qty = item['quantity']
            sub = item['subtotal']
            if len(name) > 18:
                name = name[:16] + '..'
            lines.append(f"  {name} x{qty} = {currency}{sub:,.2f}")
        if len(items) > 4:
            lines.append(f"  + {len(items) - 4} more item(s)")

    lines.append(sep)

    if discount > 0:
        lines.append(f"Discount: -{currency}{discount:,.2f}")

    lines.append(f"TOTAL: {currency}{total:,.2f}")
    lines.append(f"Payment: {method_label}")

    if payment_method == 'cash' and change_due > 0:
        lines.append(f"Change: {currency}{change_due:,.2f}")

    if loyalty_points > 0:
        lines.append(f"Loyalty pts earned: +{loyalty_points}")

    lines.append(sep)
    lines.append("We appreciate your patronage.")
    lines.append("Visit us again soon!")

    message = '\n'.join(lines)
    return send_sms(phone, message)
