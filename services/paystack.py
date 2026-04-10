import requests
from flask import current_app

PAYSTACK_BASE = 'https://api.paystack.co'


def _headers():
    return {
        'Authorization': f'Bearer {current_app.config["PAYSTACK_SECRET_KEY"]}',
        'Content-Type': 'application/json'
    }


def initialize_transaction(amount_ghs, email='customer@pixxxel.com', channels=None):
    """
    Initialize a Paystack transaction — returns access_code and reference.
    channels: e.g. ['mobile_money'] or ['card'] or None for all channels.
    """
    payload = {
        'email': email,
        'amount': int(round(amount_ghs * 100)),  # pesewas
        'currency': 'GHS',
    }
    if channels:
        payload['channels'] = channels

    resp = requests.post(f'{PAYSTACK_BASE}/transaction/initialize', json=payload, headers=_headers(), timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if not data.get('status'):
        raise Exception(data.get('message', 'Paystack error'))
    return data['data']  # contains access_code, reference, authorization_url


def verify_transaction(reference):
    """Verify final status of a transaction."""
    resp = requests.get(f'{PAYSTACK_BASE}/transaction/verify/{reference}', headers=_headers(), timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if not data.get('status'):
        raise Exception(data.get('message', 'Paystack error'))
    return data['data']
