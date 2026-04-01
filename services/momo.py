import uuid
import base64
import requests
from flask import current_app


def _base_url():
    env = current_app.config.get('MOMO_ENVIRONMENT', 'sandbox')
    if env == 'sandbox':
        return 'https://sandbox.momodeveloper.mtn.com'
    return 'https://momodeveloper.mtn.com'


def _get_access_token():
    """Get OAuth2 Bearer token using API user credentials."""
    api_user = current_app.config['MOMO_API_USER_ID']
    api_key  = current_app.config['MOMO_API_KEY']
    sub_key  = current_app.config['MOMO_SUBSCRIPTION_KEY']

    credentials = base64.b64encode(f"{api_user}:{api_key}".encode()).decode()

    resp = requests.post(
        f"{_base_url()}/collection/token/",
        headers={
            'Authorization': f'Basic {credentials}',
            'Ocp-Apim-Subscription-Key': sub_key,
        },
        timeout=15
    )
    resp.raise_for_status()
    return resp.json()['access_token']


def format_phone(phone: str) -> str:
    """Convert Ghana phone number to international format (233XXXXXXXXX)."""
    phone = phone.strip().replace(' ', '').replace('-', '')
    if phone.startswith('0') and len(phone) == 10:
        return '233' + phone[1:]
    if phone.startswith('+233'):
        return phone[1:]  # remove +
    return phone


def request_to_pay(phone: str, amount: float, note: str = 'Payment') -> dict:
    """
    Send a USSD payment prompt to the customer's phone.
    Returns {'reference_id': str} on success, raises on failure.
    """
    token   = _get_access_token()
    sub_key = current_app.config['MOMO_SUBSCRIPTION_KEY']
    env     = current_app.config.get('MOMO_ENVIRONMENT', 'sandbox')
    ref_id  = str(uuid.uuid4())

    payload = {
        'amount': str(int(amount)),       # MTN expects integer string
        'currency': 'GHS' if env != 'sandbox' else 'EUR',  # sandbox uses EUR
        'externalId': ref_id,
        'payer': {
            'partyIdType': 'MSISDN',
            'partyId': format_phone(phone)
        },
        'payerMessage': note,
        'payeeNote': note,
    }

    resp = requests.post(
        f"{_base_url()}/collection/v1_0/requesttopay",
        json=payload,
        headers={
            'Authorization': f'Bearer {token}',
            'Ocp-Apim-Subscription-Key': sub_key,
            'X-Reference-Id': ref_id,
            'X-Target-Environment': env,
            'Content-Type': 'application/json',
        },
        timeout=15
    )

    if resp.status_code != 202:
        raise Exception(f"MoMo request failed: {resp.status_code} {resp.text}")

    return {'reference_id': ref_id}


def get_payment_status(reference_id: str) -> dict:
    """
    Poll the status of a payment request.
    Returns dict with 'status': 'PENDING' | 'SUCCESSFUL' | 'FAILED'
    """
    token   = _get_access_token()
    sub_key = current_app.config['MOMO_SUBSCRIPTION_KEY']
    env     = current_app.config.get('MOMO_ENVIRONMENT', 'sandbox')

    resp = requests.get(
        f"{_base_url()}/collection/v1_0/requesttopay/{reference_id}",
        headers={
            'Authorization': f'Bearer {token}',
            'Ocp-Apim-Subscription-Key': sub_key,
            'X-Target-Environment': env,
        },
        timeout=15
    )
    resp.raise_for_status()
    data = resp.json()
    return {
        'status': data.get('status', 'PENDING'),
        'reason': data.get('reason', ''),
        'reference_id': reference_id,
    }
