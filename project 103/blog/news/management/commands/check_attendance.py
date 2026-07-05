from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from news.models import TrainerSchedule, AttendanceLog, names
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
    help = 'Check today\'s attendance vs schedule and notify admin of missed shifts'

    def handle(self, *args, **options):
        today = timezone.now()
        today_date = today.date()
        py_weekday = today_date.weekday()
        schedule_weekday = (py_weekday + 1) % 7

        trainers = names.objects.filter(role='trainer')
        missed = []

        for trainer in trainers:
            schedules = trainer.schedules.filter(day_of_week=schedule_weekday)
            if not schedules:
                continue
            checked_in = AttendanceLog.objects.filter(
                member=trainer,
                check_in__date=today_date,
            ).exists()
            if not checked_in:
                shifts = ', '.join(f'{s.get_shift_display()} ({s.shift_start()}–{s.shift_end()})' for s in schedules)
                missed.append(f'{trainer.name}: {shifts}')

        if missed:
            today_str = today_date.strftime('%A %d/%m/%Y')
            msg = f'⚠️ *Missed Attendance – {today_str}*\n\n'
            msg += '\n'.join(missed)
            msg += '\n\nNo check-in recorded for these trainers.'
            send_telegram_message(msg)
            self.stdout.write(self.style.SUCCESS(f'Notification sent for {len(missed)} trainer(s)'))
        else:
            self.stdout.write(self.style.SUCCESS('All scheduled trainers checked in today'))
