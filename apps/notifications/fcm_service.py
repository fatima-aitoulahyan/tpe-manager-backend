import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings

if not firebase_admin._apps:
    cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
    firebase_admin.initialize_app(cred)


def send_push_notification(token: str, title: str, body: str, data: dict = None):
    message = messaging.Message(
        notification=messaging.Notification(title=title, body=body),
        data=data or {},
        token=token,
    )
    try:
        response = messaging.send(message)
        return response
    except messaging.UnregisteredError:
        return None
    except Exception as e:
        print(f"FCM Error: {e}")
        return None


def send_multicast(tokens: list[str], title: str, body: str, data: dict = None):
    message = messaging.MulticastMessage(
        notification=messaging.Notification(title=title, body=body),
        data=data or {},
        tokens=tokens,
    )
    response = messaging.send_each_for_multicast(message)
    return response