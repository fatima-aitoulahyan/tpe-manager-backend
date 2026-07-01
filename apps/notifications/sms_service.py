from twilio.rest import Client
from django.conf import settings


def format_phone_maroc(telephone: str) -> str:
    tel = telephone.strip().replace(' ', '').replace('-', '')
    if tel.startswith('0'):
        return '+212' + tel[1:]
    if tel.startswith('+212'):
        return tel
    return tel


def send_sms(to: str, message: str):
    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        msg = client.messages.create(
            body=message,
            messaging_service_sid=settings.TWILIO_MESSAGING_SERVICE_SID,  # ← au lieu de from_
            to=to
        )
        print(f'SMS envoyé à {to} - SID: {msg.sid}')
        return msg.sid
    except Exception as e:
        print(f'SMS Error: {e}')
        return None