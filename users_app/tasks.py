from django.core.mail import send_mail
from config.celery import app
from django.conf import settings
from users_app.models import AuthType
from shared_app.utils import send_sms


@app.task()
def send_email_or_sms(auth_type, email_subject=None, email_message=None, email=None, phone_number=None):
    if auth_type == AuthType.email:
        print(f"sending email to {email}")
        send_mail(
            subject=email_subject,
            message=email_message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[email],
            fail_silently=False,
        )

    elif auth_type == AuthType.phone:
        send_sms(
            phone_number=phone_number,
        )
