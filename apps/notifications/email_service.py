from django.core.mail import EmailMessage
from django.core.mail.backends.smtp import EmailBackend


def send_email_as_vendeur(vendeur, to: str, subject: str, body: str) -> bool:
    config = getattr(vendeur, 'config_email', None)

    if not config or not all([
        config.email_host,
        config.email_address,
        config.email_password,
    ]):
        print(f"Configuration email incomplète pour {vendeur.email}")
        return False

    try:
        backend = EmailBackend(
            host=config.email_host,
            port=config.email_port,
            username=config.email_address,
            password=config.email_password,
            use_tls=config.email_use_tls,
            fail_silently=False,
        )

        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=f"{vendeur.nom} {vendeur.prenom} <{config.email_address}>",
            to=[to],
            connection=backend,
        )
        email.send()
        print(f"Email envoyé de {config.email_address} vers {to}")
        return True

    except Exception as e:
        print(f"Email Error: {e}")
        return False