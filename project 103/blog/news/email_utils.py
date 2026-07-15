import threading
import logging
from django.core.mail import send_mail
from django.conf import settings
from pathlib import Path

logger = logging.getLogger(__name__)

ERROR_LOG_FILE = Path(__file__).parent.parent / 'email_errors.log'


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
            error_msg = f"Failed to send email to {recipient_list}: {e}\n"
            logger.error(error_msg)
            try:
                with open(ERROR_LOG_FILE, 'a') as f:
                    f.write(error_msg)
            except:
                pass

    thread = threading.Thread(target=_send)
    thread.start()
