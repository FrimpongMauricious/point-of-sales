import requests
from flask import current_app

PAYSTACK_BASE = 'https://api.paystack.co'


def _headers():
    return {
        'Authorization': f'Bearer {current_app.config["PAYSTACK_SECRET_KEY"]}',
        'Content-Type': 'application/json'
    }


def initiate_mobile_money(phone, amount_ghs, provider='mtn', email='customer@pixxxel.com'):
    """
    Initiate a Ghana mobile money charge via Paystack.
    provider: 'mtn' | 'vod' (Vodafone) | 'tgo' (AirtelTigo)
    Returns Paystack data dict with 'reference' and 'status'.
    """
    payload = {
        'email': email,
        'amount': int(round(amount_ghs * 100)),  # pesewas
        'currency': 'GHS',
        'mobile_money': {
            'phone': phone,
            'provider': provider
        }
    }
    resp = requests.post(f'{PAYSTACK_BASE}/charge', json=payload, headers=_headers(), timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if not data.get('status'):
        raise Exception(data.get('message', 'Paystack error'))
    return data['data']


def initiate_card(card_number, expiry_month, expiry_year, cvv, amount_ghs, email='customer@pixxxel.com'):
    """
    Initiate a card charge via Paystack direct charge API.
    Returns Paystack data dict — status may be 'send_otp', 'send_pin', or 'success'.
    """
    payload = {
        'email': email,
        'amount': int(round(amount_ghs * 100)),  # pesewas
        'currency': 'GHS',
        'card': {
            'number': card_number.replace(' ', ''),
            'cvv': cvv,
            'expiry_month': str(expiry_month).zfill(2),
            'expiry_year': str(expiry_year)
        }
    }
    resp = requests.post(f'{PAYSTACK_BASE}/charge', json=payload, headers=_headers(), timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if not data.get('status'):
        raise Exception(data.get('message', 'Paystack error'))
    return data['data']


def submit_otp(otp, reference):
    """Submit OTP for mobile money or card charge."""
    payload = {'otp': str(otp).strip(), 'reference': reference}
    resp = requests.post(f'{PAYSTACK_BASE}/charge/submit_otp', json=payload, headers=_headers(), timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if not data.get('status'):
        raise Exception(data.get('message', 'Paystack error'))
    return data['data']


def submit_pin(pin, reference):
    """Submit card PIN when Paystack requests it."""
    payload = {'pin': str(pin).strip(), 'reference': reference}
    resp = requests.post(f'{PAYSTACK_BASE}/charge/submit_pin', json=payload, headers=_headers(), timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if not data.get('status'):
        raise Exception(data.get('message', 'Paystack error'))
    return data['data']


def verify_transaction(reference):
    """Verify final status of a transaction."""
    resp = requests.get(f'{PAYSTACK_BASE}/transaction/verify/{reference}', headers=_headers(), timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if not data.get('status'):
        raise Exception(data.get('message', 'Paystack error'))
    return data['data']
