from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import timedelta
from news.models import MembershipPayment, questions, response_model
import requests

TELEGRAM_BOT_TOKEN = '8906420648:AAHcpw_RXOH91wQ9XG2Tp3_B8cm65rnuoDU'
TELEGRAM_CHAT_ID = '-5141645804'

def send_telegram_message(message_text):
    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
    try:
        requests.post(url, json={'chat_id': TELEGRAM_CHAT_ID, 'text': message_text, 'parse_mode': 'Markdown'})
    except requests.exceptions.RequestException as e:
        print(f'Telegram error: {e}')

class Command(BaseCommand):
    help = 'Notify trainees whose subscription expires in 7 days'

    def handle(self, *args, **options):
        today = timezone.now().date()
        expiry_date = today + timedelta(days=7)

        expiring_payments = MembershipPayment.objects.filter(
            subscription_end=expiry_date,
            is_verified=True,
        ).select_related('user')

        notified = []

        for payment in expiring_payments:
            user = payment.user
            marker = f"Subscription Expiry Notice – {expiry_date.strftime('%d/%m/%Y')}"

            already_sent = questions.objects.filter(
                name=user.username,
                quest=marker,
            ).exists()

            if already_sent:
                continue

            q = questions.objects.create(
                name=user.username,
                email=user.email or '',
                quest=marker,
            )

            response_model.objects.create(
                name=user,
                quest=q,
                text=(
                    f"Hi {user.username},\n\n"
                    f"Your gym subscription will expire on {expiry_date.strftime('%A, %d %B %Y')} (7 days from now).\n"
                    f"Please renew your membership to continue enjoying full gym access.\n\n"
                    f"Thank you,\nFuture Gym Team"
                ),
            )

            notified.append(user.username)

        if notified:
            msg = f"🔔 *Subscription Expiry Notices – {today.strftime('%d/%m/%Y')}*\n\n"
            msg += f"Sent reminders to {len(notified)} trainee(s):\n"
            msg += '\n'.join(f"• {name}" for name in notified)
            send_telegram_message(msg)
            self.stdout.write(self.style.SUCCESS(f'Notified {len(notified)} trainee(s)'))
        else:
            self.stdout.write(self.style.SUCCESS('No subscriptions expiring in 7 days'))
