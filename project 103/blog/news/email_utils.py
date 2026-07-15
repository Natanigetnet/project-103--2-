import threading
import logging
import requests
from django.conf import settings
from pathlib import Path

logger = logging.getLogger(__name__)

ERROR_LOG_FILE = Path(__file__).parent.parent / 'email_errors.log'


def send_email_async(subject, message, recipient_list, fail_silently=True):
    def _send():
        try:
            api_key = getattr(settings, 'SENDGRID_API_KEY', '')
            if not api_key:
                raise ValueError("SENDGRID_API_KEY not configured")
            
            from_email = settings.DEFAULT_FROM_EMAIL
            to_emails = recipient_list if isinstance(recipient_list, list) else [recipient_list]
            
            payload = {
                "personalizations": [{"to": [{"email": email} for email in to_emails]}],
                "from": {"email": from_email},
                "subject": subject,
                "content": [{"type": "text/plain", "value": message}]
            }
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                "https://api.sendgrid.com/v3/mail/send",
                json=payload,
                headers=headers,
                timeout=10
            )
            
            if response.status_code not in [200, 201, 202]:
                raise Exception(f"SendGrid API error: {response.status_code} - {response.text}")
                
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
