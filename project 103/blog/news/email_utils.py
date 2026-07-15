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
            api_key = getattr(settings, 'RESEND_API_KEY', '')
            if not api_key:
                raise ValueError("RESEND_API_KEY not configured")
            
            from_email = getattr(settings, 'RESEND_FROM_EMAIL', 'onboarding@resend.dev')
            to_emails = recipient_list if isinstance(recipient_list, list) else [recipient_list]
            
            payload = {
                "from": from_email,
                "to": to_emails,
                "subject": subject,
                "text": message
            }
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                "https://api.resend.com/emails",
                json=payload,
                headers=headers,
                timeout=10
            )
            
            if response.status_code not in [200, 201]:
                raise Exception(f"Resend API error: {response.status_code} - {response.text}")
                
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
