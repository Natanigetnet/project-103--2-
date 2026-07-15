import threading
import logging
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)


def send_email_async(subject, message, recipient_list, fail_silently=True):
    def _send():
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                recipient_list,
                fail_silently=fail_silently,
            )
        except Exception as e:
            logger.error(f"Failed to send email to {recipient_list}: {e}")

    thread = threading.Thread(target=_send)
    thread.start()
