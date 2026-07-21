from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import HttpResponse
from django.utils.html import format_html   
from .models import names,comments,Category,questions,response_model,TrainingSession,BodyMetric,TrainingSpace,MemberID,AttendanceLog,TrainerRating,TrainerChangeRequest,TrainingPlan,TrainingPlanDay,TrainerPayment,TrainerSchedule,GymConfig,SplitProgression
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.backends import ModelBackend
from django.contrib import messages
from functools import wraps
from django.db.models import Avg, Count, Q, Sum, DecimalField
from django.db.models.functions import TruncMonth, Coalesce
from datetime import datetime, timedelta

class CaseInsensitiveAuthBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = User
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        try:
            user = UserModel._default_manager.get(username__iexact=username)
        except UserModel.DoesNotExist:
            return None
        else:
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        return None
from .forms import UserRegisterForm, TraineeAccountForm, TraineeMedicalForm, ethiopian_phone_validator
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import MembershipPayment
from django.utils import timezone
import requests
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import UserProfile
from .email_utils import send_email_async
import uuid
from django.core.validators import RegexValidator
import secrets
import string

import json

@user_passes_test(lambda u: u.is_superuser, login_url='login_url')
def admin_dash(request):
    from datetime import date
    config = GymConfig.objects.first()
    if not config:
        config = GymConfig.objects.create(payment_day=1)
    upcoming_payments = []
    for tp in TrainerPayment.objects.select_related('trainer').all():
        days = tp.days_until_payment
        if days is not None and 0 <= days <= 3:
            upcoming_payments.append({
                'trainer_name': tp.trainer.name,
                'salary': tp.salary,
                'next_due': tp.next_payment_due,
                'days_until': days,
            })
    return render(request, 'admin.html', {'upcoming_payments': upcoming_payments, 'config': config})

@user_passes_test(lambda u: u.is_superuser, login_url='login_url')
def gym_config_view(request):
    config = GymConfig.objects.first()
    if not config:
        config = GymConfig.objects.create(payment_day=1)
    if request.method == 'POST':
        payment_day = request.POST.get('payment_day')
        if payment_day:
            payment_day = int(payment_day)
            if 1 <= payment_day <= 28:
                config.payment_day = payment_day
                config.save()
                messages.success(request, f'Global payment day updated to day {payment_day} of each month.')
                return redirect('gym_config_url')
            else:
                messages.error(request, 'Payment day must be between 1 and 28.')
    return render(request, 'gym_config.html', {'config': config})

@user_passes_test(lambda u: u.is_superuser, login_url='login_url')
def trainer_schedules_list(request):
    if request.method == 'POST':
        trainer_id = request.POST.get('trainer')
        days = request.POST.getlist('days')
        shifts = request.POST.getlist('shifts')
        if trainer_id and days and shifts:
            count = 0
            for day in days:
                for shift in shifts:
                    _, created = TrainerSchedule.objects.get_or_create(
                        trainer_id=trainer_id,
                        day_of_week=day,
                        shift=shift,
                    )
                    if created:
                        count += 1
            messages.success(request, f'{count} schedule entries added.')
            return redirect('trainer_schedules_url')
    trainers = names.objects.filter(role='trainer').order_by('name')
    schedules = TrainerSchedule.objects.select_related('trainer').all().order_by('trainer__name', 'day_of_week')
    from itertools import groupby
    grouped = [(k, list(g)) for k, g in groupby(schedules, key=lambda s: s.trainer.name)]
    return render(request, 'trainer_schedules.html', {
        'trainers': trainers,
        'grouped_schedules': grouped,
        'schedules': schedules,
        'day_choices': TrainerSchedule.DAY_CHOICES,
        'shift_choices': TrainerSchedule.SHIFT_CHOICES,
    })

@user_passes_test(lambda u: u.is_superuser, login_url='login_url')
def trainer_schedule_edit(request, schedule_id):
    schedule = get_object_or_404(TrainerSchedule, id=schedule_id)
    if request.method == 'POST':
        trainer_id = request.POST.get('trainer')
        day_of_week = request.POST.get('day_of_week')
        shift = request.POST.get('shift')
        if trainer_id and day_of_week and shift:
            schedule.trainer_id = trainer_id
            schedule.day_of_week = day_of_week
            schedule.shift = shift
            schedule.save()
            messages.success(request, 'Schedule updated.')
            return redirect('trainer_schedules_url')
    trainers = names.objects.filter(role='trainer').order_by('name')
    return render(request, 'trainer_schedule_edit.html', {'schedule': schedule, 'trainers': trainers})

@user_passes_test(lambda u: u.is_superuser, login_url='login_url')
def trainer_schedule_delete(request, schedule_id):
    schedule = get_object_or_404(TrainerSchedule, id=schedule_id)
    schedule.delete()
    messages.success(request, 'Schedule entry deleted.')
    return redirect('trainer_schedules_url')

@user_passes_test(lambda u: u.is_superuser, login_url='login_url')
def employee_payment_edit(request, payment_id):
    payment = get_object_or_404(TrainerPayment, id=payment_id)
    if request.method == 'POST':
        trainer_id = request.POST.get('employee')
        salary = request.POST.get('salary')
        payment_frequency = request.POST.get('payment_frequency', 'monthly')
        last_payment_date = request.POST.get('last_payment_date') or None
        notes = request.POST.get('notes', '')
        if trainer_id and salary:
            payment.trainer_id = trainer_id
            payment.salary = salary
            payment.payment_frequency = payment_frequency
            payment.last_payment_date = last_payment_date
            payment.notes = notes
            payment.save()
            messages.success(request, 'Payment record updated.')
            return redirect('employee_payments_url')
    employees = names.objects.filter(role__in=['trainer', 'trainee']).order_by('name')
    return render(request, 'employee_payment_edit.html', {'payment': payment, 'employees': employees})

@user_passes_test(lambda u: u.is_superuser, login_url='login_url')
def employee_payment_delete(request, payment_id):
    payment = get_object_or_404(TrainerPayment, id=payment_id)
    trainer_name = payment.trainer.name
    payment.delete()
    messages.success(request, f'Payment record deleted for {trainer_name}.')
    return redirect('employee_payments_url')

@user_passes_test(lambda u: u.is_superuser, login_url='login_url')
def employee_payments_list(request):
    config = GymConfig.objects.first()
    if not config:
        config = GymConfig.objects.create(payment_day=1)

    if request.method == 'POST':
        employee_id = request.POST.get('employee')
        salary = request.POST.get('salary')
        payment_frequency = request.POST.get('payment_frequency', 'monthly')
        last_payment_date = request.POST.get('last_payment_date') or None
        notes = request.POST.get('notes', '')
        if employee_id and salary:
            emp = get_object_or_404(names, id=employee_id)
            TrainerPayment.objects.update_or_create(
                trainer=emp,
                defaults={
                    'salary': salary,
                    'payment_frequency': payment_frequency,
                    'last_payment_date': last_payment_date,
                    'notes': notes,
                }
            )
            messages.success(request, f'Payment record saved for {emp.name}.')
            return redirect('employee_payments_url')

    # Gather all employees: trainers + registrars
    employee_records = []
    seen_names = set()

    # Trainers: names with role='trainer'
    for n in names.objects.filter(role='trainer').order_by('name'):
        key = (n.name.lower(), n.email or '')
        if key not in seen_names:
            seen_names.add(key)
            payment = getattr(n, 'payment_info', None)
            employee_records.append({
                'id': n.id,
                'name': n.name,
                'email': n.email,
                'role': 'Trainer',
                'names_record': n,
                'payment': payment,
            })

    # Registrars: UserProfile with role='registrar', find linked names via email
    for up in UserProfile.objects.filter(role='registrar').select_related('user'):
        user = up.user
        n = names.objects.filter(email__iexact=user.email).first()
        if n:
            key = (n.name.lower(), n.email or '')
            if key not in seen_names:
                seen_names.add(key)
                payment = getattr(n, 'payment_info', None)
                employee_records.append({
                    'id': n.id,
                    'name': n.name,
                    'email': n.email,
                    'role': 'Registrar',
                    'names_record': n,
                    'payment': payment,
                })
        else:
            # No names record found — create one so payment can be assigned
            n = names.objects.create(name=user.get_full_name() or user.username, email=user.email, role='trainee')
            payment = getattr(n, 'payment_info', None)
            employee_records.append({
                'id': n.id,
                'name': n.name,
                'email': n.email,
                'role': 'Registrar',
                'names_record': n,
                'payment': payment,
            })

    employee_records.sort(key=lambda r: r['name'].lower())

    payments = TrainerPayment.objects.select_related('trainer').all().order_by('trainer__name')
    return render(request, 'employee_payments.html', {
        'employees': employee_records,
        'payments': payments,
        'config': config,
    })

@user_passes_test(lambda u: u.is_superuser, login_url='login_url')
def admin_trainer_dashboard(request):
    from datetime import timedelta, date
    import calendar

    today = timezone.now()
    today_date = today.date()

    # Week boundaries: Sunday-Saturday (Israeli convention)
    days_since_sunday = (today_date.weekday() + 1) % 7
    week_start = today_date - timedelta(days=days_since_sunday)
    week_end = week_start + timedelta(days=6)

    # Month boundaries
    month_start = today_date.replace(day=1)

    # Build list of days in current month for checking scheduled vs attended
    if month_start.month == 12:
        next_month = month_start.replace(year=month_start.year + 1, month=1)
    else:
        next_month = month_start.replace(month=month_start.month + 1)
    month_end = next_month - timedelta(days=1)

    # Query all trainers
    trainers = names.objects.filter(role='trainer').order_by('name')

    trainer_data = []
    for trainer in trainers:
        payment_info = getattr(trainer, 'payment_info', None)

        schedules = list(trainer.schedules.all().order_by('day_of_week'))

        # Attendance logs this month
        monthly_logs = AttendanceLog.objects.filter(
            member=trainer,
            check_in__date__gte=month_start,
            check_in__date__lte=month_end,
        ).order_by('check_in')

        # Total hours this month
        total_seconds = 0
        attended_dates = set()
        for log in monthly_logs:
            if log.check_out:
                duration = log.check_out - log.check_in
                total_seconds += duration.total_seconds()
            attended_dates.add(log.check_in.date())

        monthly_hours = round(total_seconds / 3600, 1)

        # Scheduled days this month vs attended
        scheduled_days = set()
        missed_days = []
        cur = month_start
        while cur <= month_end:
            py_weekday = cur.weekday()
            schedule_weekday = (py_weekday + 1) % 7  # convert to our Sun=0..Sat=6
            day_schedules = [s for s in schedules if s.day_of_week == schedule_weekday]
            if day_schedules:
                scheduled_days.add(cur)
                if cur not in attended_dates:
                    missed_days.append({
                        'date': cur,
                        'start': day_schedules[0].shift_start(),
                        'end': day_schedules[0].shift_end(),
                    })
            cur += timedelta(days=1)

        scheduled_count = len(scheduled_days)
        attendance_rate = round(len(attended_dates) / scheduled_count * 100, 1) if scheduled_count > 0 else 0

        # Monthly calendar (all weeks in the month)
        month_weeks = []
        # Find the Sunday on or before month_start
        month_py_weekday = month_start.weekday()
        month_schedule_weekday = (month_py_weekday + 1) % 7
        calendar_start = month_start - timedelta(days=month_schedule_weekday)
        
        cur_week_start = calendar_start
        while cur_week_start <= month_end:
            week_days = []
            for i in range(7):
                day_date = cur_week_start + timedelta(days=i)
                py_weekday = day_date.weekday()
                schedule_weekday = (py_weekday + 1) % 7
                day_schedules = [s for s in schedules if s.day_of_week == schedule_weekday]
                was_present = day_date in attended_dates
                in_month = month_start <= day_date <= month_end
                week_days.append({
                    'date': day_date,
                    'day_name': ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'][schedule_weekday],
                    'scheduled': day_schedules[0] if day_schedules else None,
                    'was_present': was_present,
                    'in_month': in_month,
                })
            month_weeks.append({
                'week_number': len(month_weeks) + 1,
                'days': week_days,
            })
            cur_week_start += timedelta(weeks=1)

        # Last 10 missed days
        missed_recent = sorted(missed_days, key=lambda x: x['date'], reverse=True)[:10]

        # Next payment info
        days_until = payment_info.days_until_payment if payment_info else None

        trainer_data.append({
            'trainer': trainer,
            'payment_info': payment_info,
            'schedules': schedules,
            'monthly_hours': monthly_hours,
            'attended_count': len(attended_dates),
            'scheduled_count': scheduled_count,
            'missed_count': len(missed_days),
            'attendance_rate': attendance_rate,
            'month_weeks': month_weeks,
            'missed_recent': missed_recent,
            'days_until_payment': days_until,
        })

    return render(request, 'admin_trainer_dashboard.html', {
        'trainer_data': trainer_data,
        'week_start': week_start,
        'week_end': week_end,
        'month_start': month_start,
        'month_end': month_end,
        'today': today_date,
    })

def signup(request):
    is_admin = request.user.is_authenticated and request.user.is_superuser
    if request.method == "POST":
        form = UserRegisterForm(request.POST, require_profile_fields=not is_admin)
        if not is_admin:
            form.fields.pop('role', None)
            form.fields.pop('category', None)
        if form.is_valid():
            user = form.save()
            role = form.cleaned_data.get('role') or UserProfile.ROLE_TRAINEE
            gender = form.cleaned_data.get('gender')
            category = form.cleaned_data.get('category') if role == UserProfile.ROLE_TRAINER else None
            UserProfile.objects.update_or_create(user=user, defaults={'role': role, 'gender': gender, 'category': category})

            full_name = (form.cleaned_data.get('full_name') or '').strip()
            phone_number = (form.cleaned_data.get('phone_number') or '').strip()
            if full_name:
                parts = full_name.split(None, 1)
                user.first_name = parts[0]
                user.last_name = parts[1] if len(parts) > 1 else ''
                user.save(update_fields=['first_name', 'last_name'])

            username = form.cleaned_data.get('username')
            email = (form.cleaned_data.get('email') or user.email or '').strip()
            if email and user.email != email:
                user.email = email
                user.save(update_fields=['email'])

            if role == UserProfile.ROLE_TRAINEE and full_name:
                names.objects.create(
                    name=full_name,
                    email=email or user.email,
                    phone_number=phone_number,
                    detail='Joined via website signup',
                    role=names.ROLE_TRAINEE,
                    gender=gender,
                )

            email_sent = False
            display_name = full_name or username
            if email and not is_admin:
                subject = "Welcome to Future Gym - Registration Successful"
                message = f"""Dear {display_name},

Thank you for joining Future Gym! Your registration was successful.

You can sign in with the username and password you chose during signup.

Username: {username}
Email: {email}

If you did not create this account, please contact the gym administration.

Best regards,
Future Gym Management
"""
                send_email_async(subject, message, [email])
                email_sent = True

            # Attempt to log the new user in immediately
            raw_password = form.cleaned_data.get('password1')
            authenticated_user = authenticate(username=user.username, password=raw_password)
            if authenticated_user is not None:
                login(request, authenticated_user)
                if email_sent:
                    messages.success(
                        request,
                        f"Welcome, {username}! Your account has been created and a confirmation email was sent to {email}.",
                    )
                else:
                    messages.success(
                        request,
                        f"Welcome, {username}! Your account has been created and you are now signed in.",
                    )
                return redirect('home_url')
            else:
                if email_sent:
                    messages.success(
                        request,
                        f"Account created for {username}! A confirmation email was sent to {email}. Please sign in.",
                    )
                else:
                    messages.success(request, f"Account created for {username}! Please sign in.")
                return redirect('login_url')
    else:
        form = UserRegisterForm(require_profile_fields=not is_admin)
        if not is_admin:
            form.fields.pop('role', None)
            form.fields.pop('category', None)
    return render(request, 'signup.html', {'form': form, 'is_admin': is_admin})

def loginUser(request):
    if request.method == "POST":
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            is_first_login = user.last_login is None
            login(request, user)
            if is_first_login and not user.is_superuser and hasattr(user, 'profile') and user.profile.role in (UserProfile.ROLE_TRAINEE, UserProfile.ROLE_TRAINER):
                messages.success(request, format_html('For security, please change your password in account details. Click <a href="{}" class="alert-link">here</a> to update.', reverse('password_change_url')))
            return redirect('home_url')
        else:
            messages.error(request, "Invalid username or password.")
    form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def logoutUser(request):
    logout(request) 
    return redirect('login_url')
@user_passes_test(lambda u: u.is_superuser, login_url='login_url')
def user_list(request):
    return render(request, 'manage_users_branch.html')

@user_passes_test(lambda u: u.is_superuser, login_url='login_url')
def manage_members(request):
    profiles = UserProfile.objects.filter(role=UserProfile.ROLE_TRAINEE).exclude(user__is_superuser=True).select_related('user', 'category').order_by('-user__date_joined')
    rows = []
    for profile in profiles:
        linked_name = names.objects.filter(trainer=profile.user).first()
        rows.append({
            'id': profile.user.id,
            'username': profile.user.username,
            'email': profile.user.email,
            'role_label': 'Trainee',
            'joined': profile.user.date_joined,
            'is_superuser': profile.user.is_superuser,
            'is_user': True,
            'name_record': linked_name.name if linked_name else None,
        })

    existing_emails = [row['email'] for row in rows if row['email']]
    superuser_emails = list(User.objects.filter(is_superuser=True).values_list('email', flat=True))
    legacy_members = names.objects.filter(role=names.ROLE_TRAINEE).exclude(email__in=existing_emails).exclude(email__in=superuser_emails).order_by('-date')
    for member in legacy_members:
        rows.append({
            'id': member.id,
            'username': member.name or 'Unknown',
            'email': member.email or 'No email',
            'role_label': 'Trainee (Legacy)',
            'joined': member.date,
            'is_superuser': False,
            'is_user': False,
            'legacy_id': member.id,
            'name_record': member.name,
        })

    return render(request, 'user_management.html', {
        'rows': rows,
        'title': 'Manage Members',
        'subtitle': 'Trainee accounts created by admin',
        'action_label': 'New Member',
        'create_url': 'register_url',
        'delete_redirect': 'manage_members_url',
    })

@user_passes_test(lambda u: u.is_superuser, login_url='login_url')
def manage_staff(request):
    profiles = UserProfile.objects.filter(role__in=[UserProfile.ROLE_TRAINER, UserProfile.ROLE_REGISTRAR]).exclude(user__is_superuser=True).select_related('user', 'category').order_by('-user__date_joined')
    rows = []
    for profile in profiles:
        linked_name = names.objects.filter(trainer=profile.user).first()
        role_labels = {UserProfile.ROLE_TRAINER: 'Trainer', UserProfile.ROLE_REGISTRAR: 'Registrar'}
        rows.append({
            'id': profile.user.id,
            'username': profile.user.username,
            'email': profile.user.email,
            'role_label': role_labels.get(profile.role, profile.role),
            'joined': profile.user.date_joined,
            'is_superuser': profile.user.is_superuser,
            'is_user': True,
            'name_record': linked_name.name if linked_name else None,
        })

    existing_emails = [row['email'] for row in rows if row['email']]
    superuser_emails = list(User.objects.filter(is_superuser=True).values_list('email', flat=True))
    legacy_trainers = names.objects.filter(role=names.ROLE_TRAINER).exclude(email__in=existing_emails).exclude(email__in=superuser_emails).order_by('-date')
    for trainer in legacy_trainers:
        rows.append({
            'id': trainer.id,
            'username': trainer.name or 'Unknown',
            'email': trainer.email or 'No email',
            'role_label': 'Trainer (Legacy)',
            'joined': trainer.date,
            'is_superuser': False,
            'is_user': False,
            'legacy_id': trainer.id,
            'name_record': trainer.name,
        })

    return render(request, 'user_management.html', {
        'rows': rows,
        'title': 'Manage Staff',
        'subtitle': 'Registrar and Trainer accounts',
        'action_label': 'New Employee',
        'create_url': 'register_url',
        'delete_redirect': 'manage_staff_url',
    })


def notify_trainer_of_assignment(trainer_user, member, assigned_by=None):
    """In-app message when a trainee is assigned to a trainer."""
    trainee_name = member.name or 'Trainee'
    category_label = member.category.name if member.category else 'Not set'
    phone = member.phone_number or '—'
    trainee_email = member.email or '—'

    notice_email = member.email or trainer_user.email or 'noreply@futuregym.com'
    notice = questions.objects.create(
        name=trainer_user.username,
        email=notice_email,
        quest=f'New assignment: {trainee_name}',
    )
    response_model.objects.create(
        name=assigned_by,
        quest=notice,
        text=(
            f'You have been assigned a new trainee: {trainee_name}. '
            f'Category: {category_label}. Phone: {phone}. Email: {trainee_email}.'
        ),
        is_read=False,
    )


def _trainers_for_member_category(all_trainers, member):
    """Trainers whose profile category matches the trainee's category."""
    member_category_id = member.category_id
    matching = [
        t for t in all_trainers
        if (t.profile.category_id == member_category_id)
        or (member_category_id is None and t.profile.category_id is None)
    ]
    if member.trainer_id and member.trainer_id not in {t.id for t in matching}:
        assigned = next((t for t in all_trainers if t.id == member.trainer_id), None)
        if assigned:
            matching = list(matching) + [assigned]
    return matching


@user_passes_test(lambda u: u.is_superuser, login_url='login_url')
def assign_trainer(request):
    """Admin page to assign existing members to trainers."""
    all_trainers = list(
        User.objects.filter(profile__role=UserProfile.ROLE_TRAINER)
        .select_related('profile', 'profile__category')
        .order_by('username')
    )
    members_base = names.objects.filter(role=names.ROLE_TRAINEE).select_related('trainer', 'category', 'preferred_trainer')

    if request.method == 'POST':
        notifications_sent = 0
        for member in members_base.select_related('trainer', 'category'):
            old_trainer_id = member.trainer_id

            cat_key = f"category_{member.id}"
            if cat_key in request.POST:
                raw_cat = request.POST.get(cat_key, '').strip()
                if not raw_cat or raw_cat == 'none':
                    member.category = None
                else:
                    try:
                        member.category_id = int(raw_cat)
                    except (TypeError, ValueError):
                        pass
                member.save()
                if member.email:
                    UserProfile.objects.filter(
                        user__email__iexact=member.email,
                        role=UserProfile.ROLE_TRAINEE,
                    ).update(category=member.category)

            trainer_val = request.POST.get(f"trainer_{member.id}")
            if trainer_val is None:
                continue
            trainer_val = trainer_val.strip()
            if trainer_val == "":
                member.trainer = None
            else:
                try:
                    trainer_user = User.objects.get(
                        id=int(trainer_val),
                        profile__role=UserProfile.ROLE_TRAINER,
                    )
                    member.trainer = trainer_user
                except (User.DoesNotExist, ValueError):
                    continue
            member.save()

            if member.trainer_id and member.trainer_id != old_trainer_id:
                notify_trainer_of_assignment(member.trainer, member, request.user)
                notifications_sent += 1

        if notifications_sent:
            messages.success(
                request,
                f"Assignments updated. {notifications_sent} trainer(s) notified by email and Messages.",
            )
        else:
            messages.success(request, "Assignments updated.")
        return redirect('assign_trainer_url')

    members_qs = members_base.order_by('-date')
    member_rows = [
        {
            'member': member,
            'trainers': _trainers_for_member_category(all_trainers, member),
            'preferred_id': member.preferred_trainer_id,
        }
        for member in members_qs
    ]
    categories = Category.objects.all().order_by('name')
    trainers_json = json.dumps([
        {
            'id': t.id,
            'username': t.username,
            'email': t.email or '',
            'category_id': t.profile.category_id,
        }
        for t in all_trainers
    ])
    return render(request, 'assign_trainer.html', {
        'member_rows': member_rows,
        'categories': categories,
        'trainers_json': trainers_json,
    })

@user_passes_test(lambda u: u.is_superuser, login_url='login_url')
def delete_user(request, user_id):
    user_to_delete = get_object_or_404(User, id=user_id)
    if not user_to_delete.is_superuser:
        names.objects.filter(email__iexact=user_to_delete.email).delete()
        user_to_delete.delete()
        messages.success(request, "User deleted successfully.")
    return redirect(request.META.get('HTTP_REFERER', 'user_management_url'))

@user_passes_test(lambda u: u.is_superuser, login_url='login_url')
def delete_legacy_member(request, member_id):
    member = get_object_or_404(names, id=member_id)
    member.delete()
    messages.success(request, "Legacy member deleted successfully.")
    return redirect(request.META.get('HTTP_REFERER', 'manage_users_url'))

@user_passes_test(lambda u: u.is_superuser, login_url='login_url')
def edit_legacy_member(request, member_id):
    member_obj = get_object_or_404(names, id=member_id)
    return edit(request, member_obj.name)


def home(request):
    unread_count = 0
    is_trainee = False
    is_registrar = False
    spaces_for_modal = []
    upcoming_sessions = []
    if request.user.is_authenticated:
        if request.user.is_superuser:
            unread_count = response_model.objects.filter(is_read=False).count()
        else:
            unread_count = response_model.objects.filter(
                quest__email__iexact=request.user.email,
                is_read=False,
            ).count()
            profile = UserProfile.objects.filter(user=request.user).first()
            is_trainee = bool(profile and profile.role == UserProfile.ROLE_TRAINEE)
            is_registrar = bool(profile and profile.role == UserProfile.ROLE_REGISTRAR)
            if profile and profile.is_trainer and profile.category:
                spaces_for_modal = TrainingSpace.objects.filter(category=profile.category).select_related('category')
            elif profile and profile.is_trainer:
                spaces_for_modal = TrainingSpace.objects.select_related('category').all()

    # Upcoming sessions grouped by category for all authenticated users
    upcoming_sessions = {}
    if request.user.is_authenticated:
        sessions_qs = TrainingSession.objects.filter(
            session_date__gte=timezone.now()
        ).select_related('trainer', 'space', 'space__category').order_by('session_date')[:20]
        for session in sessions_qs:
            cat_name = session.space.category.name if session.space and session.space.category else 'General'
            upcoming_sessions.setdefault(cat_name, []).append(session)

    assigned_trainer_name = None
    if is_trainee:
        trainee_record = names.objects.filter(email=request.user.email, role=names.ROLE_TRAINEE).first()
        if trainee_record and trainee_record.trainer:
            trainer_user = trainee_record.trainer
            trainer_name_record = names.objects.filter(email=trainer_user.email, role=names.ROLE_TRAINER).first()
            if trainer_name_record:
                assigned_trainer_name = trainer_name_record.name

    my_detail_name = None
    my_trainee_id = None
    if request.user.is_authenticated:
        my_record = names.objects.filter(
            Q(email__iexact=request.user.email) |
            Q(name__iexact=request.user.username) |
            Q(name__iexact=request.user.get_full_name())
        ).first()
        if my_record:
            my_detail_name = my_record.name
            my_trainee_id = my_record.id

    attendance_message = None
    if is_trainee and my_trainee_id:
        now = timezone.now()
        thirty_days_ago = now - timedelta(days=30)
        recent_checkins = AttendanceLog.objects.filter(
            member_id=my_trainee_id,
            check_in__gte=thirty_days_ago
        ).count()

        seven_days_ago = now - timedelta(days=7)
        last_week_checkins = AttendanceLog.objects.filter(
            member_id=my_trainee_id,
            check_in__gte=seven_days_ago
        ).count()

        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        checked_in_today = AttendanceLog.objects.filter(
            member_id=my_trainee_id,
            check_in__gte=today_start
        ).exists()

        if recent_checkins == 0:
            attendance_message = {
                'icon': 'bi-emoji-frown',
                'color': 'danger',
                'title': 'Where have you been?',
                'text': 'We miss you at the gym! Your gains are waiting for you.',
            }
        elif last_week_checkins >= 5 or recent_checkins >= 20:
            attendance_message = {
                'icon': 'bi-fire',
                'color': 'success',
                'title': 'You ain\'t missing a day, are you?',
                'text': f'{recent_checkins} workouts in the last 30 days! You\'re on another level.',
            }
        elif recent_checkins >= 8:
            attendance_message = {
                'icon': 'bi-trophy',
                'color': 'warning',
                'title': 'Consistency is key!',
                'text': f'{recent_checkins} workouts this month. Keep that momentum going!',
            }

        if checked_in_today and attendance_message:
            attendance_message['text'] += ' Great job showing up today!'

    context = {
        'unread_count': unread_count,
        'is_trainee': is_trainee,
        'is_registrar': is_registrar,
        'spaces': spaces_for_modal,
        'upcoming_sessions': upcoming_sessions,
        'assigned_trainer_name': assigned_trainer_name,
        'my_detail_name': my_detail_name,
        'my_trainee_id': my_trainee_id,
        'attendance_message': attendance_message,
    }
    return render(request, 'home.html', context)


def _require_trainee(view_func):
    @login_required(login_url='login_url')
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_superuser:
            messages.error(request, 'This section is for trainee accounts only.')
            return redirect('home_url')
        profile = UserProfile.objects.filter(user=request.user).first()
        if not profile:
            profile = UserProfile.objects.create(user=request.user, role=UserProfile.ROLE_TRAINEE)
        if profile.role != UserProfile.ROLE_TRAINEE:
            messages.error(request, 'Access restricted to trainees.')
            return redirect('home_url')
        request.trainee_profile = profile
        return view_func(request, *args, **kwargs)
    return wrapper


def _get_trainee_name_record(user):
    if user.email:
        record = names.objects.filter(role=names.ROLE_TRAINEE, email__iexact=user.email).first()
        if record:
            return record
    return names.objects.filter(role=names.ROLE_TRAINEE, trainer=user).first()


def _trainee_account_initial(user, profile):
    record = _get_trainee_name_record(user)
    full_name = ''
    if record and record.name:
        full_name = record.name
    else:
        full_name = user.get_full_name().strip() or user.username
    return {
        'full_name': full_name,
        'email': user.email or (record.email if record else ''),
        'phone_number': record.phone_number if record else '',
        'gender': profile.gender or '',
    }


def _sync_trainee_name_record(user, profile, full_name, phone, email):
    record = _get_trainee_name_record(user)
    if not record:
        names.objects.create(
            name=full_name,
            email=email,
            phone_number=phone,
            detail='Trainee account',
            role=names.ROLE_TRAINEE,
            gender=profile.gender,
            trainer=user,
        )
        return
    record.name = full_name
    record.email = email
    record.phone_number = phone
    record.gender = profile.gender
    record.save(update_fields=['name', 'email', 'phone_number', 'gender'])


def _require_trainer(view_func):
    @login_required(login_url='login_url')
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        profile = UserProfile.objects.filter(user=request.user).first()
        if not profile or profile.role != UserProfile.ROLE_TRAINER:
            messages.error(request, 'Access restricted to trainers.')
            return redirect('home_url')
        request.trainer_profile = profile
        return view_func(request, *args, **kwargs)
    return wrapper


def _get_trainer_name_record(user):
    return names.objects.filter(role=names.ROLE_TRAINER, trainer=user).first()


def _trainer_account_initial(user, profile):
    record = _get_trainer_name_record(user)
    full_name = ''
    if record and record.name:
        full_name = record.name
    else:
        full_name = user.get_full_name().strip() or user.username
    return {
        'full_name': full_name,
        'email': user.email or (record.email if record else ''),
        'phone_number': record.phone_number if record else '',
        'gender': profile.gender or '',
    }


def _sync_trainer_name_record(user, profile, full_name, phone, email):
    record = _get_trainer_name_record(user)
    if not record:
        names.objects.create(
            name=full_name,
            email=email,
            phone_number=phone,
            detail='Trainer account',
            role=names.ROLE_TRAINER,
            gender=profile.gender,
            trainer=user,
        )
        return
    record.name = full_name
    record.email = email
    record.phone_number = phone
    record.gender = profile.gender
    record.save(update_fields=['name', 'email', 'phone_number', 'gender'])


@_require_trainer
def trainer_settings(request):
    profile = request.trainer_profile
    return render(request, 'trainer_settings.html', {
        'profile': profile,
    })


@_require_trainer
def trainer_update_account(request):
    profile = request.trainer_profile
    user = request.user
    initial = _trainer_account_initial(user, profile)

    if request.method == 'POST':
        form = TraineeAccountForm(request.POST, request.FILES, exclude_user=user)
        if form.is_valid():
            full_name = form.cleaned_data['full_name'].strip()
            email = form.cleaned_data['email'].strip()
            phone = form.cleaned_data['phone_number'].strip()
            gender = form.cleaned_data.get('gender') or None
            image = form.cleaned_data.get('image')

            parts = full_name.split(None, 1)
            user.first_name = parts[0]
            user.last_name = parts[1] if len(parts) > 1 else ''
            user.email = email
            user.save(update_fields=['first_name', 'last_name', 'email'])

            profile.gender = gender
            if image:
                profile.image = image
            profile.save(update_fields=['gender', 'image'] if image else ['gender'])

            _sync_trainer_name_record(user, profile, full_name, phone, email)
            messages.success(request, 'Your account details were updated.')
            return redirect('trainer_settings_url')
    else:
        form = TraineeAccountForm(initial=initial, exclude_user=user)

    return render(request, 'trainer_account.html', {
        'form': form,
        'username': user.username,
        'profile': profile,
    })


@_require_trainee
def trainee_settings(request):
    profile = request.trainee_profile
    return render(request, 'trainee/settings.html', {
        'profile': profile,
        'has_medical_info': bool(profile.medical_info and profile.medical_info.strip()),
    })


@_require_trainee
def trainee_update_account(request):
    profile = request.trainee_profile
    user = request.user
    initial = _trainee_account_initial(user, profile)

    if request.method == 'POST':
        form = TraineeAccountForm(request.POST, request.FILES, exclude_user=user)
        if form.is_valid():
            full_name = form.cleaned_data['full_name'].strip()
            email = form.cleaned_data['email'].strip()
            phone = form.cleaned_data['phone_number'].strip()
            gender = form.cleaned_data.get('gender') or None
            image = form.cleaned_data.get('image')

            parts = full_name.split(None, 1)
            user.first_name = parts[0]
            user.last_name = parts[1] if len(parts) > 1 else ''
            user.email = email
            user.save(update_fields=['first_name', 'last_name', 'email'])

            profile.gender = gender
            if image:
                profile.image = image
            profile.save(update_fields=['gender', 'image'] if image else ['gender'])

            _sync_trainee_name_record(user, profile, full_name, phone, email)
            messages.success(request, 'Your account details were updated.')
            return redirect('trainee_settings_url')
    else:
        form = TraineeAccountForm(initial=initial, exclude_user=user)

    return render(request, 'trainee/account.html', {
        'form': form,
        'username': user.username,
        'profile': profile,
    })


@_require_trainee
def trainee_medical_info(request):
    profile = request.trainee_profile

    if request.method == 'POST':
        form = TraineeMedicalForm(request.POST)
        if form.is_valid():
            profile.medical_info = form.cleaned_data.get('medical_info', '').strip()
            profile.save(update_fields=['medical_info'])
            messages.success(request, 'Your medical information was saved.')
            return redirect('trainee_settings_url')
    else:
        form = TraineeMedicalForm(initial={'medical_info': profile.medical_info})

    return render(request, 'trainee/medical.html', {'form': form})


def landing(request):
    return render(request, 'landing.html')

def about(request):
    return render(request,'about.html')
def _get_contact_name(request):
    """Return the best display name for the current user."""
    if not request.user.is_authenticated:
        return ''
    person = _get_names_profile(request.user)
    if person:
        return person.name
    return request.user.get_full_name() or request.user.username


import re
from django.utils import timezone as tz_now

def _build_gym_context():
    parts = []

    categories = Category.objects.all()
    if categories.exists():
        lines = []
        for c in categories:
            desc = f" - {c.description}" if c.description else ""
            member_count = c.names_set.count()
            lines.append(f"  - {c.name} ({member_count} members){desc}")
        parts.append("TRAINING CATEGORIES:\n" + "\n".join(lines))

    trainers = names.objects.filter(role=names.ROLE_TRAINER).select_related('category')
    if trainers.exists():
        lines = []
        for t in trainers:
            cat = t.category.name if t.category else "General"
            trainee_count = names.objects.filter(trainer__username=t.name).count() if t.name else 0
            try:
                user_obj = User.objects.get(username=t.name)
                trainee_count = names.objects.filter(trainer=user_obj).count()
            except User.DoesNotExist:
                pass
            avg_rating = t.ratings_received.aggregate(avg=Avg('rating'))['avg']
            rating_str = f"{avg_rating:.1f}/5" if avg_rating else "No ratings yet"
            lines.append(f"  - {t.name} | Category: {cat} | Trainees: {trainee_count} | Rating: {rating_str}")
        parts.append("TRAINERS:\n" + "\n".join(lines))

    now = tz_now.now()
    upcoming = TrainingSession.objects.filter(
        session_date__gte=now
    ).select_related('trainer', 'space').order_by('session_date')[:8]
    if upcoming.exists():
        lines = []
        for s in upcoming:
            date_str = s.session_date.strftime("%b %d, %Y %I:%M %p")
            space_str = s.space.name if s.space else "TBD"
            slots = s.slots_left
            lines.append(f"  - \"{s.title}\" on {date_str} | Trainer: {s.trainer.name} | Space: {space_str} | Slots left: {slots}")
        parts.append("UPCOMING SESSIONS:\n" + "\n".join(lines))

    spaces = TrainingSpace.objects.all()
    if spaces.exists():
        lines = []
        for sp in spaces:
            status = "UNDER MAINTENANCE" if sp.is_under_maintenance else "Available"
            lines.append(f"  - {sp.name} ({sp.category.name}) - {status}")
        parts.append("TRAINING SPACES:\n" + "\n".join(lines))

    parts.append("GYM HOURS: Monday-Friday 6:00 AM - 10:00 PM, Saturday 8:00 AM - 8:00 PM, Sunday 9:00 AM - 6:00 PM")
    parts.append("GYM NAME: Future Gym")
    parts.append("LOCATION: 123 Tech Avenue, Silicon Valley, CA. Free parking available.")
    parts.append("CONTACT: +1 (555) 000-TECH | hello@futuregym.com")

    total_trainers = names.objects.filter(role=names.ROLE_TRAINER).count()
    total_trainees = names.objects.filter(role=names.ROLE_TRAINEE).count()
    parts.append(f"STATS: {total_trainers} trainers, {total_trainees} trainees, {categories.count()} categories")

    return "\n\n".join(parts)


def _build_site_guide(user_role=""):
    guide = []

    guide.append("""The website has 4 user roles: Admin (superuser), Trainer, Trainee (Member), and Registrar.
Each role has different pages and capabilities. Use the navigation bar at the top of every page to move around.
The main hub page is /home/ (the Home page). The landing page is at /.""")

    guide.append("""COMMON PAGES (all authenticated users):
- Home (/home/): Main dashboard with quick actions and overview.
- About (/about/): Information about Future Gym.
- Contact (/contact/): Send questions/messages to the admin team.
- AI Chat (/chat/): This page - ask the AI assistant anything about the gym or how to use the website.
- ID Card (/my-id-card/): View your digital member ID with QR code for gym check-in. You can also download it as PDF.
- Messages (/response_list/): View responses from trainers and admin to your questions.
- Explore Trainers (/trainers-and-types/): Browse all trainers and training categories.
- Trainer Selector (/trainer-selector/): For trainees to find and request a trainer.
- Password Change (/password-change/): Change your account password.""")

    guide.append("""TRAINEE (MEMBER) FEATURES:
- Home (/home/): See your assigned trainer, upcoming sessions from your trainer, attendance stats, and quick links.
- Settings (/settings/): Manage your trainee profile.
  - Account Details (/settings/account/): Update your name, email, phone, gender, and profile picture.
  - Medical Info (/settings/medical/): Add medical notes, conditions, or allergies for your trainer to see.
- Progress/BMI (/bmi/): Track your BMI and body metrics over time. Enter weight and height to calculate.
- Trainer Sessions (/trainer-sessions/): See all upcoming sessions created by your assigned trainer. Register or unregister for sessions here. Also shows your current training split info.
- Training Plan/Schedule (/training-plan/<your_id>/): View your weekly training schedule created by your trainer. Shows the 4-week calendar with exercises for each day, split type, and progression.
- Find Trainers (/trainer-selector/): Browse trainers by category and request assignment.
- Rate Trainer (/rate-trainer/<trainer_name>/): Give a rating (0-5) and comment for your trainer.
- Request Trainer Change (/request-trainer-change/<trainer_name>/): Submit a request to change your assigned trainer (requires a reason).
- Telegram Group: Link available in the menu to join the gym's Telegram chat.
- Check-in: Use your ID card QR code at the gym entrance to check in/out. The registrar or admin scans it.""")

    guide.append("""TRAINER FEATURES:
- Home (/home/): See your trainees, quick actions to create sessions, and links to your tools.
- "Create Session Slot" button (on Home page): Opens a modal to broadcast a new training session. Fill in title, description, date/time, duration, max capacity, and optionally select a training space. All your assigned trainees will be notified.
- Session Hub (/session/hub/): Overview page for managing your sessions.
- Create Session (/session/create/): Dedicated page to create a new training session (same as the modal).
- Session Registrations (/trainer-session-registrations/): See which trainees have registered for your upcoming sessions.
- Tracker (/tracker/): Your trainer dashboard showing all assigned trainees with stats (total members, male/female count, recent joins).
- Workout Tracking (/trainer/workout-tracking/): See each trainee's current workout based on their split progression. Shows next body part, split type, total workouts completed, and last workout date. You can reset a trainee's split progression from here.
- My Schedule (/trainer/my-schedule/): View your weekly work schedule (day/evening shifts). You can add comments to each shift slot which will be sent to admin.
- My Trainees In Gym (/trainer/currently-in/): See which of your assigned trainees are currently checked in at the gym today, and who has already left.
- Training Plan (/training-plan/<trainee_id>/): Create and manage training plans for your trainees. You can:
  - Create a new plan with a split type (Upper/Lower, Push/Pull/Legs, Full Body, Bro Split, etc.)
  - Add exercises to each day (name, sets, reps, weight, notes)
  - Mark days as rest days
  - Change the split type
  - Add general notes
  - Navigate week by week to see the 4-week calendar view
- Trainer Settings (/trainer-settings/): Manage your trainer profile.
  - Account Details (/trainer-settings/account/): Update your name, email, phone, gender, and profile picture.
  - My Schedule (/trainer/my-schedule/): View and comment on your weekly schedule.
- My Feedback (/trainer-my-feedback/): See ratings and comments from your trainees.
- Trainer Ratings Dashboard (/trainer-ratings/): View overall trainer ratings.""")

    guide.append("""REGISTRAR FEATURES:
- Home (/home/): Quick access buttons for registrar functions.
- Registrar Dashboard (/registrar/dashboard/): Overview showing who's currently in the gym, crowdedness by category, active trainers today, and recent check-ins.
- Register Trainee (/registrar/register/): Register a new trainee member. Creates their account automatically with a generated password and sends a welcome email.
- Check In (/registrar/scan-qr/): Scan member QR codes to check them into the gym.
- Check Out (/registrar/scan-checkout/): Scan member QR codes to check them out of the gym.
- Currently In Gym (/registrar/currently-in/): See all members currently checked in at the gym.
- Attendance Log (/registrar/attendance-log/): View the full attendance history.""")

    guide.append("""ADMIN (SUPERUSER) FEATURES:
- Home (/home/): Full management access with buttons for all admin functions.
- Management Menu (in navbar): Dropdown with all admin tools.
  - Members (/members/): View all trainers and trainees with their details.
  - Staff Accounts (/manage-users/): Manage user accounts (create trainers, registrars, etc.).
  - Categories (/category_list/): Manage training categories (create, edit, delete).
  - Messages (/questions-log/): View all questions from members and respond to them.
  - Record Payment (/record-payment/): Record membership payments for members.
  - Telegram Broadcast (/telegram-broadcast/): Send broadcast messages to the gym Telegram group.
  - QR Scanner (/admin/qr-scanner/): Scan member QR codes for attendance.
  - Attendance Log (/attendance-log/): View full attendance history.
  - Attendance Dashboard (/admin/attendance-dashboard/): Visual attendance analytics.
  - Core Management (/admin-portal/): Main admin portal with gym configuration.
- Admin Portal (/admin-portal/): Core management page.
- Gym Config (/admin/gym-config/): Set the global payment day (1-28) for all employee payments.
- Trainer Schedules (/admin/trainer-schedules/): Create and manage trainer weekly schedules (assign days and shifts).
- Trainer Dashboard (/admin/trainer-dashboard/): Admin view of trainer information.
- Employee Payments (/admin/employee-payments/): Manage trainer/employee salary and payment records.
- Training Spaces (/training-spaces/): Create and manage training spaces. Assign spaces to categories, toggle maintenance status.
- Generate All IDs (/admin/generate-all-ids/): Generate member ID cards for all members who don't have one.
- Regenerate All QR Codes (/admin/regenerate-all-qr-codes/): Regenerate QR codes for all members.""")

    guide.append("""NAVIGATION TIPS:
- The navbar at the top of every page has a "Menu" dropdown (three dots icon) with role-specific links.
- Admins see a "Management" dropdown in the navbar with admin tools.
- Registrars see a "Registrar" dropdown with registrar-specific links.
- Trainers see links to Tracker, Workout Tracking, My Schedule, My Trainees In Gym, and Profile in the Menu dropdown.
- Trainees see links to Settings, Progress (BMI), Telegram, and ID Card in the Menu dropdown.
- To find your trainer's detail page, click the "Trainer" link in the navbar (visible to trainees with an assigned trainer).
- The "Explore" link in the Menu shows all trainers and categories.
- The AI Chat is accessible from the Menu dropdown for all non-admin users.""")

    return "\n\n".join(guide)


def _format_history_for_prompt(history):
    if not history:
        return ""
    lines = []
    for msg in history[-10:]:
        role = "User" if msg['role'] == 'user' else "Assistant"
        lines.append(f"{role}: {msg['content']}")
    return "\n".join(lines)


_FAQ = [
    (r'(?i)^\s*(hi|hello|hey|good\s*(morning|afternoon|evening)|sup|yo|hey.?\s*there)\s*[.!?]*\s*$', (
        'Hello! Welcome to Future Gym support. How can I help you today?'
    )),
    (r'(?i)(how|where).*(trainee|member|client).*(list|page|account|dashboard|view|see|find|access)', (
        'Trainers: Go to Home, then open the Menu dropdown and click "Tracker" to see all your assigned trainees. '
        'You can also click "Workout Tracking" to see each trainee\'s current workout plan and progress.'
    )),
    (r'(?i)(how|where).*(create|make|add|broadcast).*(session|class|slot)', (
        'Trainers: From the Home page, click the green "Create Session Slot" button to open the session creation form. '
        'Fill in the title, date/time, duration, max capacity, and optionally a training space. '
        'All your assigned trainees will be notified automatically.'
    )),
    (r'(?i)(how|where).*(training|workout).*(plan|schedule|split|program|calendar)', (
        'Trainers: Go to Menu > "Workout Tracking" to see each trainee\'s split. '
        'To create or edit a training plan, go to the trainee\'s Training Plan page (linked from Workout Tracking). '
        'There you can set the split type, add exercises for each day, and manage the weekly calendar. '
        'Trainees: Go to Menu > "Schedule" or click the "Schedule" button on the Home page to view your training plan.'
    )),
    (r'(?i)(how|where).*(my|see|view|check).*(schedule|shift|work).*(trainer|my|account)', (
        'Trainers: Go to Menu > "My Schedule" to see your weekly work schedule with day/evening shifts. '
        'You can add comments to each shift slot which will be sent to the admin.'
    )),
    (r'(?i)(how|where).*(rate|review|feedback|rating).*(trainer)', (
        'Trainees: You can rate your trainer by going to your trainer\'s detail page (click "Trainer" in the navbar) '
        'and using the rate button, or by navigating to /rate-trainer/<trainer_name>/.'
    )),
    (r'(?i)(how|where).*(change|switch|request|get new).*(trainer)', (
        'Trainees: Go to your trainer\'s detail page and click "Request Trainer Change", '
        'or navigate to /request-trainer-change/<trainer_name>/. You\'ll need to provide a reason for the change.'
    )),
    (r'(?i)(how|where).*(bmi|progress|body|metric|weight|height).*(track|measure|calculate|view)', (
        'Trainees: Go to Menu > "Progress" to track your BMI and body metrics. '
        'Enter your weight and height to calculate your BMI. Trainers can also view your metrics.'
    )),
    (r'(?i)(how|where).*(medical|health|allergy|condition|note).*(info|add|update|view)', (
        'Trainees: Go to Menu > "Settings" > "Medical info" to add medical notes, conditions, or allergies. '
        'Your trainer will be able to see this information.'
    )),
    (r'(?i)(how|where).*(id|card|badge|qr).*(view|see|get|download)', (
        'Go to Menu > "ID Card" to view your digital member ID with QR code. '
        'You can download it as a PDF or regenerate the QR code if needed.'
    )),
    (r'(?i)(how|where).*(message|contact|question|ask|reply|response).*(send|view|see|check)', (
        'You can send messages to admin/trainers via the Contact page (Menu > "Contact"). '
        'Check responses in Menu > "Messages". You can also ask me (the AI assistant) anything right here!'
    )),
    (r'(?i)(how|where).*(register|sign.?up|join|new.*member|create account).*(trainee|member|user)', (
        'To join Future Gym, visit the gym and a registrar will create your account. '
        'Admins can also register new members from the Management menu. '
        'Once registered, you\'ll receive login credentials via email.'
    )),
    (r'(?i)(how|where).*(password|login|sign.?in|account).*(change|update|reset|access)', (
        'To change your password, go to Menu > "Settings" > "Change password" (or /password-change/). '
        'To log in, go to the landing page and click "Sign In".'
    )),
    (r'(?i)(how|where).*(currently.?in|who.*gym|present|checked.?in).*(trainee|member|person|people)', (
        'Trainers: Go to Menu > "My Trainees In Gym" to see which of your trainees are currently checked in. '
        'Registrars: Go to your Dashboard > "Currently In Gym" to see all members in the gym. '
        'Admins: Check the Attendance Dashboard for a full overview.'
    )),
    (r'(?i)(how|where).*(payment|pay|salary|employee|compensation).*(record|manage|view|track)', (
        'Admins: Go to Management > "Record Payment" to record member payments, '
        'or "Employee Payments" to manage trainer salaries. '
        'The global payment day can be set in Gym Config.'
    )),
    (r'(?i)(how|where).*(category|categories|type|class).*(manage|view|browse|see)', (
        'Admins: Go to Management > "Categories" to manage training categories. '
        'All users can browse categories via Menu > "Explore" to see trainers and spaces by category.'
    )),
    (r'(?i)(how|where).*(space|room|area|facility|venue).*(manage|create|view|book)', (
        'Admins: Go to Management > "Training Spaces" to create, edit, or toggle maintenance status for training spaces. '
        'Spaces are linked to categories and can be selected when creating sessions.'
    )),
    (r'(?i)(how|where).*(telegram|group|chat|broadcast).*(join|send|message)', (
        'Trainees: Find the Telegram group link in Menu > "Telegram". '
        'Admins: Use Management > "Telegram Broadcast" to send messages to the gym Telegram group.'
    )),
    (r'(?i)(how|where).*(check.?in|check.?out|attendance|scan|qr).*(record|track|view)', (
        'Use your digital ID card QR code at the gym entrance. Go to Menu > "ID Card" to view your QR code. '
        'The registrar or admin will scan it when you arrive and leave. '
        'You can also check your attendance history from the Attendance Log page.'
    )),
    (r'(?i)\b(cancel|refund|cancellation|money.back)\b', (
        'Cancellation and refund policies vary by membership type. Please speak with an '
        'admin or check your membership agreement for full details.'
    )),
    (r'(?i)\b(payment|pay|billing|invoice|receipt)\b', (
        'Payments are recorded by gym administration. If you have a billing question, '
        'please contact the front desk or submit a detailed inquiry here.'
    )),
    (r'(?i)\b(qr|id.card|scan|check.in|attendance)\b', (
        'Each member receives a digital ID card with a unique QR code. Present it at the '
        'gym entrance scanner to record your check-in. You can view and print your card '
        'from the "ID" section in your account.'
    )),
    (r'(?i)\b(bmi|body.metric|weight|height|progress|measure)\b', (
        'Track your BMI and body metrics from your account dashboard under "Progress". '
        'Trainers can also view your metrics to tailor your program.'
    )),
    (r'(?i)\b(personal.trainer|coach|trainers?|instructor)\b', (
        'We have certified trainers in Aerobics, Calisthenics, and Yoga. After registering, '
        'you can browse trainers by category and request assignment from your account dashboard.'
    )),
    (r'(?i)\b(class|session|program|workout)\b', (
        'Trainers create category-specific sessions. Check "Trainer Sessions" in your account '
        'to see available classes and register for open slots.'
    )),
    (r'(?i)(?=.*\b(?:hours?|open|close|when|time|schedule)\b)(?=.*\b(?:gym|class|session)\b)', (
        'Our gym is open Monday-Friday 6:00 AM - 10:00 PM, Saturday 8:00 AM - 8:00 PM, '
        'and Sunday 9:00 AM - 6:00 PM. Category-specific training spaces may have separate schedules.'
    )),
    (r'(?i)\b(membership|price|cost|fee|subscription|sign.?up|join)\b', (
        'Future Gym offers monthly and annual membership plans. Please contact our front desk '
        'or visit the gym for current pricing and any promotional offers.'
    )),
    (r'(?i)(?=.*\b(?:park|parking|car|location|address|directions)\b)(?!.*\b(?:find|see|view|access|trainee|member|session|schedule|plan)\b)', (
        'Future Gym is located at 123 Tech Avenue, Silicon Valley, CA. Free parking is '
        'available for members in the adjacent lot.'
    )),
    (r'(?i)\b(phone|contact|call|reach|email|support|help)\b', (
        'You can reach us at +1 (555) 000-TECH or email hello@futuregym.com. '
        'You can also submit questions here and a trainer will respond.'
    )),
    (r'(?i)\b(how|where|what page|how do i|where do i|where can i|how can i)\b.*\b(find|see|view|access|create|make|add|change|edit|update|manage|check|get|use|navigate|go)\b', (
        'Please describe what you\'re looking for in more detail. For example: '
        '"Where do I find my trainee list?" or "How do I create a session?" or "Where is my schedule?" '
        'I can help you navigate the website step by step!'
    )),
]


def _local_responder(question_text):
    for pattern, answer in _FAQ:
        if re.search(pattern, question_text):
            return answer, True
    return None, False


def ask_ai(question_text, history=None, gym_context="", site_guide="", user_role=""):
    api_key = settings.GEMINI_API_KEY
    if api_key:
        try:
            from google import genai
            client = genai.Client(api_key=api_key)

            role_context = ""
            if user_role:
                role_context = f"\nThe current user's role is: {user_role.upper()}. Tailor your navigation guidance specifically for this role."

            system_instructions = (
                "You are the AI assistant for Future Gym, a modern fitness center. "
                "You are friendly, knowledgeable, and concise. "
                "You help members with questions about gym operations, training programs, "
                "class schedules, trainer information, membership, facilities, and general fitness advice.\n\n"
                "CRITICAL INSTRUCTION: You MUST help users navigate the website. When users ask ANY of these types of questions:\n"
                "- 'Where do I find...'\n"
                "- 'How do I...'\n"
                "- 'How can I...'\n"
                "- 'Where is...'\n"
                "- 'Show me how to...'\n"
                "- 'What page do I go to for...'\n"
                "- 'How do I access...'\n"
                "You MUST use the WEBSITE NAVIGATION GUIDE below to give specific step-by-step instructions.\n\n"
                "EXAMPLES of good navigation answers:\n"
                "Q: 'Where is my trainee list?' (Trainer asking)\n"
                "A: 'Go to Home, then open the Menu dropdown (three dots icon) and click \"Tracker\". This shows all your assigned trainees with stats.'\n\n"
                "Q: 'How do I create a session?' (Trainer asking)\n"
                "A: 'From the Home page, click the green \"Create Session Slot\" button. Fill in the title, date/time, duration, and max capacity. All your trainees will be notified.'\n\n"
                "Q: 'Where can I see my schedule?' (Trainee asking)\n"
                "A: 'Go to Menu > \"Schedule\" or click the \"Schedule\" button on the Home page to view your training plan with the 4-week calendar.'\n\n"
                "IMPORTANT RULES:\n"
                "- Use the gym context data below to give accurate, specific answers referencing real trainers, categories, sessions, and spaces.\n"
                "- Use the WEBSITE NAVIGATION GUIDE to answer 'how-to' and 'where-to-find' questions about the website.\n"
                "- When explaining how to do something on the website, be specific: mention the exact page name, where to find it in the navigation bar, and what buttons to click.\n"
                "- If the user refers to something from earlier in the conversation (like 'them', 'that trainer', 'the first one'), use the conversation history to understand what they mean.\n"
                "- If a user asks about a specific trainer, category, or session by name, look it up in the context data.\n"
                "- Keep responses concise (2-4 sentences) unless the user asks for detail or step-by-step instructions.\n"
                "- If you don't know something and it's not in the context, say so honestly and suggest they contact staff.\n"
                "- If the question is completely unrelated to the gym, fitness, or health, respond with exactly: UNABLE_TO_ANSWER\n"
                f"{role_context}\n"
            )

            context_block = ""
            if gym_context:
                context_block = f"\n\nCURRENT GYM DATA:\n{gym_context}\n"

            guide_block = ""
            if site_guide:
                guide_block = f"\n\nWEBSITE NAVIGATION GUIDE:\n{site_guide}\n"

            history_block = ""
            if history:
                formatted = _format_history_for_prompt(history)
                if formatted:
                    history_block = f"\n\nCONVERSATION HISTORY (most recent at bottom):\n{formatted}\n"

            prompt = (
                f"{system_instructions}"
                f"{context_block}"
                f"{guide_block}"
                f"{history_block}"
                f"\n\nUSER'S CURRENT QUESTION: {question_text}"
            )

            response = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=prompt,
            )
            answer = response.text.strip()
            if 'UNABLE_TO_ANSWER' not in answer and len(answer) >= 10:
                return answer, True
        except Exception:
            pass

    return _local_responder(question_text)


def chat_page(request):
    user_name = ""
    if request.user.is_authenticated:
        user_name = _get_contact_name(request)
    return render(request, 'chat.html', {'user_name': user_name})

@require_http_methods(["POST"])
def chat_api(request):
    try:
        data = json.loads(request.body)
        message = data.get('message', '')
        client_history = data.get('history', [])
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({'error': 'Invalid request'}, status=400)

    if not message.strip():
        return JsonResponse({'error': 'Message is required'}, status=400)

    history = []
    for msg in client_history[-10:]:
        role = msg.get('role', '')
        content = msg.get('content', '')
        if role in ('user', 'bot') and content:
            history.append({'role': role, 'content': content[:1000]})

    gym_context = _build_gym_context()
    site_guide = _build_site_guide()

    user_role = ""
    if request.user.is_authenticated:
        if request.user.is_superuser:
            user_role = "admin"
        else:
            profile = UserProfile.objects.filter(user=request.user).first()
            if profile:
                user_role = profile.role

    answer, answered = ask_ai(message, history=history, gym_context=gym_context, site_guide=site_guide, user_role=user_role)

    if answered:
        if request.user.is_authenticated:
            try:
                user_name = _get_contact_name(request)
                user_email = request.user.email or ''
                q = questions(name=user_name, email=user_email, quest=message, ai_answered=True)
                q.save()
                resp = response_model(quest=q, text=answer[:500])
                resp.save()
                resp.is_read = True
                resp.save()
            except Exception:
                pass
        return JsonResponse({'answered': True, 'text': answer})
    else:
        return JsonResponse({'answered': False, 'text': ''})


def contact(request):
    user_name = _get_contact_name(request)
    user_email = request.user.email if request.user.is_authenticated else ''
    if request.method=='POST':
        name = request.POST.get('full name') or user_name
        email = request.POST.get('email') or user_email
        quest = request.POST.get('question')
        question = questions(name=name, email=email, quest=quest)
        question.save()
        messages.success(request, 'Your question has been sent to the admin team.')
        return redirect('contact_url')
    return render(request, 'contact.html', {
        'user_name': user_name,
        'user_email': user_email,
    })
@user_passes_test(lambda u: u.is_superuser, login_url='login_url')
def members(request):
    trainers = names.objects.filter(role=names.ROLE_TRAINER).order_by('-date')
    trainees = names.objects.filter(role=names.ROLE_TRAINEE).order_by('-date')

    def enrich(queryset):
        result = []
        for member in queryset:
            user_obj = None
            if member.trainer:
                user_obj = member.trainer
            elif member.email:
                user_obj = User.objects.filter(email=member.email).first()
            result.append({'names_record': member, 'user': user_obj})
        return result

    return render(request, 'members.html', {
        'trainers': enrich(trainers),
        'trainees': enrich(trainees),
        'trainers_count': trainers.count(),
        'trainees_count': trainees.count(),
    })

@login_required(login_url='login_url')
def trainer_tracker(request):
    """Trainer dashboard showing assigned members/trainees."""
    user_profile = UserProfile.objects.filter(user=request.user).first()
    
    # Redirect non-trainers
    if not user_profile or not user_profile.is_trainer:
        messages.error(request, "Access restricted to trainers only.")
        return redirect('home_url')
    
    # Get all TRAINEES assigned to this trainer (exclude other trainers)
    assigned_members = names.objects.filter(trainer=request.user, role=names.ROLE_TRAINEE).select_related('category').order_by('-date')
    
    # Compile stats
    stats = {
        'total_members': assigned_members.count(),
        'male_count': assigned_members.filter(gender=names.GENDER_MALE).count(),
        'female_count': assigned_members.filter(gender=names.GENDER_FEMALE).count(),
        'recent_joins': assigned_members.order_by('-date')[:5],
    }
    
    return render(request, 'trainer_tracker.html', {
        'members': assigned_members,
        'profile': user_profile,
        'stats': stats,
    })


@login_required(login_url='login_url')
def trainer_workout_tracking(request):
    """Trainer view showing each trainee's next workout based on their split."""
    user_profile = UserProfile.objects.filter(user=request.user).first()
    
    if not user_profile or not user_profile.is_trainer:
        messages.error(request, "Access restricted to trainers only.")
        return redirect('home_url')
    
    assigned_members = names.objects.filter(trainer=request.user, role=names.ROLE_TRAINEE).select_related('category').order_by('name')
    
    trainee_workouts = []
    for trainee in assigned_members:
        plan = TrainingPlan.objects.filter(trainee=trainee, is_active=True).first()
        progression, _ = SplitProgression.objects.get_or_create(trainee=trainee)
        
        next_body_part = None
        split_type_display = None
        if plan and plan.split_days:
            day_index = progression.current_day_index % len(plan.split_days)
            next_body_part = plan.split_days[day_index]
            split_type_display = plan.get_split_type_display()
        
        trainee_workouts.append({
            'trainee': trainee,
            'plan': plan,
            'progression': progression,
            'next_body_part': next_body_part,
            'split_type_display': split_type_display,
            'total_workouts': progression.total_workouts_completed,
            'last_workout': progression.last_workout_date,
        })
    
    return render(request, 'trainer_workout_tracking.html', {
        'trainee_workouts': trainee_workouts,
        'profile': user_profile,
    })


@login_required(login_url='login_url')
def reset_trainee_split(request, trainee_id):
    """Reset a trainee's split progression to day 0."""
    user_profile = UserProfile.objects.filter(user=request.user).first()
    
    if not user_profile or not user_profile.is_trainer:
        messages.error(request, "Access restricted to trainers only.")
        return redirect('home_url')
    
    trainee = get_object_or_404(names, id=trainee_id, trainer=request.user, role=names.ROLE_TRAINEE)
    progression, _ = SplitProgression.objects.get_or_create(trainee=trainee)
    progression.reset()
    
    messages.success(request, f'{trainee.name}\'s split progression has been reset to Day 1.')
    return redirect('trainer_workout_tracking_url')


@login_required
def trainer_session_registrations(request):
    user_profile = UserProfile.objects.filter(user=request.user).first()
    if not user_profile or not user_profile.is_trainer:
        messages.error(request, "Access restricted to trainers only.")
        return redirect('home_url')

    trainer_profile = names.objects.filter(
        email__iexact=request.user.email,
        role=names.ROLE_TRAINER
    ).first()
    if not trainer_profile:
        messages.error(request, "Trainer profile not found for your account.")
        return redirect('home_url')

    sessions = TrainingSession.objects.filter(trainer=trainer_profile, session_date__gte=timezone.now()).prefetch_related('registered_trainees').order_by('session_date')

    return render(request, 'trainer_session_registrations.html', {
        'trainer_profile': trainer_profile,
        'sessions': sessions,
    })


def Category_view(request,category_name):
    category_names = names.objects.filter(category__name=category_name).order_by('-date')
    return render(request,'home.html',{'names':category_names})

def category_catalog(request, category_name):
    category = get_object_or_404(Category, name__iexact=category_name.strip())
    spaces = TrainingSpace.objects.filter(category=category).select_related('category')
    trainers = names.objects.filter(category=category, role=names.ROLE_TRAINER).select_related('trainer')
    upcoming_sessions = TrainingSession.objects.filter(
        trainer__category=category,
        session_date__gte=timezone.now()
    ).select_related('trainer', 'space').order_by('session_date')[:10]
    return render(request, 'category_catalog.html', {
        'category': category,
        'spaces': spaces,
        'trainers': trainers,
        'upcoming_sessions': upcoming_sessions,
    })
@user_passes_test(lambda u: u.is_superuser, login_url='login_url')
def register(request):
    all_categories = Category.objects.all()

    if request.method == 'POST':
        name = request.POST.get('full_name')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        detail = request.POST.get('detail')
        gender = request.POST.get('gender')
        role = request.POST.get('role') or names.ROLE_TRAINEE
        category_id = request.POST.get('category') if role == names.ROLE_TRAINER else None
        image = request.FILES.get('profile_image')

        if role == names.ROLE_TRAINER and not category_id:
            messages.error(request, "A trainer must be assigned to a category.")
            return render(request, 'register.html', {'categories': all_categories})

        if email:
            email_lower = email.strip().lower()
            if User.objects.filter(email__iexact=email_lower).exists():
                messages.error(request, 'A user with this email address already exists.')
                return render(request, 'register.html', {'categories': all_categories})
            if names.objects.filter(email__iexact=email_lower).exists():
                messages.error(request, 'A member with this email address already exists.')
                return render(request, 'register.html', {'categories': all_categories})

        if phone_number:
            try:
                ethiopian_phone_validator(phone_number)
            except Exception:
                messages.error(request, 'Phone number must be a valid Ethiopian format (e.g. +251912345678 or 0912345678).')
                return render(request, 'register.html', {'categories': all_categories})
            if names.objects.filter(phone_number=phone_number).exists():
                messages.error(request, 'A member with this phone number already exists.')
                return render(request, 'register.html', {'categories': all_categories})

        # Generate username from name (sanitized)
        username_base = name.lower().replace(' ', '').replace('-', '')[:15]
        username = username_base
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{username_base}{counter}"
            counter += 1

        # Generate random 8-digit password
        password = ''.join(secrets.choice(string.digits) for _ in range(8))

        # Create User account
        try:
            user = User.objects.create_user(username=username, email=email, password=password)
            user.first_name = name.split()[0] if ' ' in name else name
            user.last_name = ' '.join(name.split()[1:]) if ' ' in name else ''
            user.save()

            # Create UserProfile for the user
            UserProfile.objects.get_or_create(
                user=user,
                defaults={'role': role, 'gender': gender, 'category_id': category_id}
            )
        except Exception as e:
            messages.error(request, f"Error creating user account: {str(e)}")
            return render(request, 'register.html', {'categories': all_categories})

        # Create names object
        names.objects.create(
            name=name,
            email=email,
            phone_number=phone_number,
            detail=detail,
            gender=gender,
            role=role,
            category_id=category_id,
            image=image,
        )

        subject = f"Welcome to Future Gym - Your Account Details"
        role_label = "Trainer" if role == names.ROLE_TRAINER else "Trainee"
        message = f"""
Dear {name},

Welcome to Future Gym! Your account has been successfully created.

Here are your login credentials:

Username: {username}
Password: {password}
Role: {role_label}
Email: {email}

Please log in to the system and change your password immediately for security purposes.

If you have any questions, please contact the gym administration.

Best regards,
Future Gym Management
            """

        send_email_async(subject, message, [email])
        messages.success(request, f"Account created successfully! Credentials sent to {email}")

        return redirect('members_url')

    return render(request, 'register.html', {'categories': all_categories})


@user_passes_test(lambda u: u.is_superuser, login_url='login_url')
def create_desk(request):
    if request.method == 'POST':
        name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone_number', '').strip()
        password = request.POST.get('password', '').strip()
        confirm = request.POST.get('confirm_password', '').strip()

        if not all([name, email, password]):
            messages.error(request, "Name, email, and password are required.")
            return render(request, 'create_desk.html')
        if password != confirm:
            messages.error(request, "Passwords do not match.")
            return render(request, 'create_desk.html')
        if len(password) < 8:
            messages.error(request, "Password must be at least 8 characters.")
            return render(request, 'create_desk.html')

        email_lower = email.lower()
        if User.objects.filter(email__iexact=email_lower).exists():
            messages.error(request, 'A user with this email already exists.')
            return render(request, 'create_desk.html')
        if names.objects.filter(email__iexact=email_lower).exists():
            messages.error(request, 'A member with this email already exists.')
            return render(request, 'create_desk.html')

        if phone:
            try:
                ethiopian_phone_validator(phone)
            except Exception:
                messages.error(request, 'Phone number must be a valid Ethiopian format (e.g. +251912345678 or 0912345678).')
                return render(request, 'create_desk.html')
            if names.objects.filter(phone_number=phone).exists():
                messages.error(request, 'A member with this phone number already exists.')
                return render(request, 'create_desk.html')

        username_base = name.lower().replace(' ', '').replace('-', '')[:15]
        username = username_base
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{username_base}{counter}"
            counter += 1

        try:
            user = User.objects.create_user(username=username, email=email, password=password)
            user.first_name = name.split()[0] if ' ' in name else name
            user.last_name = ' '.join(name.split()[1:]) if ' ' in name else ''
            user.save()

            UserProfile.objects.create(user=user, role=UserProfile.ROLE_REGISTRAR)

            names.objects.create(name=name, email=email, phone_number=phone, role=names.ROLE_TRAINEE)

            messages.success(request, f"Desk account '{name}' created. Username: {username}")
        except Exception as e:
            messages.error(request, f"Error creating desk account: {str(e)}")
            return render(request, 'create_desk.html')

        return redirect('manage_staff_url')

    return render(request, 'create_desk.html')


def detail(request, name):
    member = get_object_or_404(names, name=name)
    is_admin_or_trainer = request.user.is_authenticated and (
        request.user.is_superuser or (
            hasattr(request.user, 'profile') and request.user.profile.role == UserProfile.ROLE_TRAINER
        )
    )

    is_assigned_trainer = request.user.is_authenticated and (
        member.trainer == request.user
    )

    is_trainee_of_trainer = False
    if request.user.is_authenticated and member.role == names.ROLE_TRAINER:
        trainer_user = User.objects.filter(email=member.email).first()
        if trainer_user:
            is_trainee_of_trainer = names.objects.filter(
                email=request.user.email, role=names.ROLE_TRAINEE, trainer=trainer_user
            ).exists()

    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request, 'You must be logged in to send a message.')
            return redirect('login_url')
        rating_val = request.POST.get('rating')
        if rating_val is not None:
            if not is_trainee_of_trainer:
                messages.error(request, 'You are not authorized to rate this trainer.')
                return redirect('detail_url', name=member.name)
            if not rating_val or not rating_val.isdigit() or int(rating_val) not in range(6):
                messages.error(request, 'Please select a valid rating between 0 and 5.')
                return redirect('detail_url', name=member.name)
            trainee_record = names.objects.filter(email=request.user.email, role=names.ROLE_TRAINEE).first()
            if trainee_record and member.role == names.ROLE_TRAINER:
                existing, created = TrainerRating.objects.update_or_create(
                    trainee=trainee_record, trainer=member,
                    defaults={'rating': int(rating_val), 'comment': request.POST.get('comment', '').strip()}
                )
                if created:
                    messages.success(request, f'Thank you! You rated {member.name} {rating_val}/5.')
                else:
                    messages.success(request, f'Your rating for {member.name} has been updated to {rating_val}/5.')
            return redirect('detail_url', name=member.name)
        if not is_admin_or_trainer:
            messages.error(request, 'Only admins and trainers can send messages.')
            return redirect('detail_url', name=member.name)
        msg_text = request.POST.get('message_text', '').strip()
        if msg_text and member.email:
            target_user = User.objects.filter(email=member.email).first()
            if target_user:
                sender_names_record = names.objects.filter(email=request.user.email).first()
                sender_name = sender_names_record.name if sender_names_record else (request.user.get_full_name() or request.user.username)
                notification = questions.objects.create(
                    name=sender_name,
                    email=request.user.email or '',
                    quest=f'Message to {member.name}: {msg_text[:100]}',
                )
                response_model.objects.create(
                    name=request.user,
                    quest=notification,
                    text=msg_text,
                    is_read=False,
                )
                messages.success(request, f'Message sent to {member.name}.')
            else:
                messages.error(request, 'Could not find user account for this member.')
        else:
            messages.error(request, 'Message cannot be empty.')
        return redirect('detail_url', name=member.name)

    body_metrics = []
    bmi_progress = None
    medical_info = None
    target_user = None
    attendance_logs = []
    if request.user.is_authenticated and (is_assigned_trainer or request.user.is_superuser):
        attendance_logs = AttendanceLog.objects.filter(member=member).select_related('checked_in_by').order_by('-check_in')[:20]
    if is_assigned_trainer and member.email:
        target_user = User.objects.filter(email=member.email).first()
        if target_user:
            body_metrics = BodyMetric.objects.filter(user=target_user).order_by('-recorded_at')
            if body_metrics.count() >= 2:
                bmi_progress = {
                    'weight_change': round(body_metrics[0].weight - body_metrics[1].weight, 1),
                    'bmi_change': round(body_metrics[0].bmi - body_metrics[1].bmi, 1),
                }
            user_profile = UserProfile.objects.filter(user=target_user).first()
            if user_profile and user_profile.medical_info:
                medical_info = user_profile.medical_info

    existing_rating = None
    if is_trainee_of_trainer and member.role == names.ROLE_TRAINER:
        trainee_record = names.objects.filter(email=request.user.email, role=names.ROLE_TRAINEE).first()
        if trainee_record:
            existing_rating = TrainerRating.objects.filter(trainee=trainee_record, trainer=member).first()

    is_viewing_own_profile = False
    trainer_rating_stats = None
    if request.user.is_authenticated:
        profile_user = User.objects.filter(email=member.email).first()
        if profile_user and request.user == profile_user:
            is_viewing_own_profile = True
        if member.role == names.ROLE_TRAINER:
            stats = TrainerRating.objects.filter(trainer=member).aggregate(
                avg_rating=Avg('rating'), count=Count('id')
            )
            if stats['count']:
                trainer_rating_stats = stats

    return render(request, 'detail.html', {
        'name': member,
        'is_admin_or_trainer': is_admin_or_trainer,
        'is_assigned_trainer': is_assigned_trainer,
        'is_trainee_of_trainer': is_trainee_of_trainer,
        'is_viewing_own_profile': is_viewing_own_profile,
        'trainer_rating_stats': trainer_rating_stats,
        'existing_rating': existing_rating,
        'body_metrics': body_metrics,
        'bmi_progress': bmi_progress,
        'medical_info': medical_info,
        'attendance_logs': attendance_logs,
    })

@login_required
def request_trainer_change(request, trainer_name):
    trainer = get_object_or_404(names, name=trainer_name, role=names.ROLE_TRAINER)
    trainee = names.objects.filter(email=request.user.email, role=names.ROLE_TRAINEE).first()
    if not trainee:
        messages.error(request, 'You must be a registered trainee to request a trainer change.')
        return redirect('detail_url', name=trainer_name)

    if request.method == 'POST':
        reason = request.POST.get('reason', '').strip()
        if not reason:
            messages.error(request, 'Please provide a reason for the trainer change request.')
            return redirect('detail_url', name=trainer_name)

        TrainerChangeRequest.objects.create(
            trainee=trainee,
            current_trainer=trainer,
            reason=reason,
        )

        # Notify all superusers via the questions/response_model system
        superusers = User.objects.filter(is_superuser=True)
        for admin in superusers:
            notification = questions.objects.create(
                name=trainee.name,
                email=trainee.email or '',
                quest=f'Trainer change request: {trainee.name} wants to leave {trainer.name}',
            )
            response_model.objects.create(
                name=request.user,
                quest=notification,
                text=f'Trainee {trainee.name} ({trainee.email}) wants to change from trainer {trainer.name}.\n\nReason: {reason}',
                is_read=False,
            )

        messages.success(request, f'Your request to change from trainer "{trainer.name}" has been submitted to the admin.')
        return redirect('detail_url', name=trainer_name)

    return redirect('detail_url', name=trainer_name)


@login_required
def user_profile(request, user_id):
    """Display public profile of a user, hiding sensitive info like medical details, age, email, phone."""
    target_user = get_object_or_404(User, id=user_id)
    user_profile_obj = UserProfile.objects.filter(user=target_user).first()
    names_record = names.objects.filter(
        Q(email__iexact=target_user.email) |
        Q(name__iexact=target_user.username) |
        Q(name__iexact=target_user.get_full_name())
    ).first()
    
    # Build public profile data (exclude: email, phone, medical_info, age, contact details)
    profile_data = {
        'username': target_user.username,
        'first_name': target_user.first_name,
        'last_name': target_user.last_name,
        'role': user_profile_obj.role if user_profile_obj else None,
        'gender': user_profile_obj.gender if user_profile_obj else None,
        'category': user_profile_obj.category if user_profile_obj else None,
        'joined_date': target_user.date_joined,
    }
    
    return render(request, 'user_profile.html', {
        'profile': profile_data,
        'target_user': target_user,
        'names_record': names_record,
    })
def category_list(request):
    if request.method == 'POST':
        cat_name = request.POST.get('category_name')
        cat_description = request.POST.get('description', '')
        
        if cat_name:
            obj = Category()
            obj.name = cat_name
            obj.description = cat_description
            obj.save()
            return redirect('cat_list_url')

    all_categories = Category.objects.all()
    return render(request, 'cat_list.html', {'categories': all_categories})
def delete_cat(request, cat_id):
    cat = get_object_or_404(Category, id=cat_id)
    cat.delete()
    return redirect('cat_list_url')
def cat_edit(request, cat_id):
    category = get_object_or_404(Category, id=cat_id)

    if request.method == 'POST':
        new_name = request.POST.get('category_name')
        new_description = request.POST.get('description', '')
        if new_name:
            category.name = new_name
            category.description = new_description
            category.save()
            return redirect('cat_list_url')

    return render(request, 'cat_edit.html', {'category': category})
@login_required
def ques_list(request):
    if request.user.is_superuser:
        response_model.objects.filter(is_read=False).update(is_read=True)
        question = questions.objects.all().order_by('-id')
    else:
        question = questions.objects.filter(
            Q(email=request.user.email) |
            Q(response_model__name=request.user)
        ).distinct().order_by('-id')
    
    return render(request, 'ques_list.html', {'quest': question})
def ques_edit(request, q_id):
    item = get_object_or_404(questions, id=q_id)
    sender_resp = item.response_model_set.first()
    if not sender_resp or sender_resp.name != request.user:
        messages.error(request, 'You can only edit your own messages.')
        return redirect('ques_list_url')

    if request.method == 'POST':
        item.name = request.POST.get('user_name')
        item.email = request.POST.get('user_email')
        item.quest = request.POST.get('user_quest')
        item.save()
        return redirect('ques_list_url')

    return render(request, 'ques_edit.html', {'item': item})
def ques_delete(request,q_id):
    item=get_object_or_404(questions, id=q_id)
    sender_resp = item.response_model_set.first()
    if not sender_resp or sender_resp.name != request.user:
        messages.error(request, 'You can only delete your own messages.')
        return redirect('ques_list_url')
    item.delete()
    return redirect('ques_list_url')
@user_passes_test(lambda u: u.is_superuser, login_url='login_url')
def response(request, q_id):
    # Fetch the specific question being answered
    question_obj = get_object_or_404(questions, id=q_id)

    if request.method == 'POST':
        answer_text = request.POST.get('answer_text')
        
        if answer_text:
            new_response = response_model() 
            new_response.name = request.user
            new_response.quest = question_obj
            new_response.text = answer_text
            new_response.save()
            
            messages.success(request, "Your response has been recorded.")
            return redirect('ques_list_url')

    return render(request, 'response.html', {'question': question_obj})
@login_required
def response_list(request):
    if request.user.is_superuser:
        response_model.objects.filter(is_read=False).update(is_read=True)
        responses = response_model.objects.all().order_by('-id')
    else:
        response_model.objects.filter(
            quest__email__iexact=request.user.email,
            is_read=False
        ).update(is_read=True)

        responses = response_model.objects.filter(
            quest__email__iexact=request.user.email
        ).order_by('-id')
    
    return render(request, 'response_list.html', {'responses': responses})
@user_passes_test(lambda u: u.is_superuser, login_url='login_url')
def response_delete(request,r_id):
    resp=get_object_or_404(response_model,id=r_id)
    resp.delete()
    return redirect('response_list_url')


@user_passes_test(lambda u: u.is_superuser, login_url='login_url')
def response_edit(request,r_id):
    resp=get_object_or_404(response_model,id=r_id)
    if request.method == 'POST':
        resp.text = request.POST.get('text')
        resp.save()
        return redirect('response_list_url')

    return render(request, 'response_edit.html', {'item': resp})



def newpeeps(request):
    memb=comments.objects.all()
    if request.method=='POST':
        name=request.POST.get('name')
        detail=request.POST.get('detail')
        Category=request.POST.get('category')

        obj=comments()
        obj.comment=comment
        obj.save()
    return render(request,'anonymous_com.html',{'cComments':cComments})
def edit(request, name):
    member = get_object_or_404(names, name=name)
    
    if request.method == 'POST':
        member.name = request.POST.get('full_name')
        member.detail = request.POST.get('detail')
        member.gender = request.POST.get('gender')
        member.category_id = request.POST.get('category')        
        new_image = request.FILES.get('profile_image')
        if new_image:
            member.image = new_image
            
        member.save()

    all_categories = Category.objects.all()
    return render(request, 'edit.html', {
        'member': member,
        'categories': all_categories
    })
def delete_member(request, name):
    member = get_object_or_404(names, name=name)
    member.delete()
    return redirect('home_url')
def comm_edit(request, comment_id):
    comment_item = get_object_or_404(comments, id=comment_id)
    
    if request.method == 'POST':
        updated_text = request.POST.get('user_comment')
        
        if updated_text:
            comment_item.comment = updated_text
            comment_item.save()
            
           
            return redirect('detail_url', name=comment_item.post.name)

    return render(request, 'comm_edit.html', {'comment': comment_item})
    
def comm_delete(request, comment_id):
    com = get_object_or_404(comments, id=comment_id)
    
    member_name = com.post.name
    
    com.delete()
    
    return redirect('detail_url', name=member_name)


from .models import MembershipPayment, questions, response_model # Import your messaging models

def record_payment(request):
    # Fetch all users for the selection menu
    all_gym_users = User.objects.all().order_by('username') 
    selected_user_id = request.GET.get('user_id')

    if request.method == 'POST':
        u_id = request.POST.get('user_id')
        amount = request.POST.get('amount')
        method = request.POST.get('method')
        date = request.POST.get('payment_date')
        
        # Get the actual User object (This fixes the ValueError)
        target_user = get_object_or_404(User, id=u_id)
        
        # 1. Create the payment record
        MembershipPayment.objects.create(
            user=target_user,
            amount=amount,
            payment_method=method,
            payment_date=date,
            is_verified=True
        )

        # 2. Create the Inquiry/Question entry (Permanent record for user)
        receipt_notice = questions.objects.create(
            name=target_user.username,
            email=target_user.email,
            quest=f"Payment Logged: {amount} via {method} on {date}."
        )

        # 3. Create the Response entry
        # We pass 'name=target_user' as the object instance, not a string
        response_model.objects.create(
            name=target_user, 
            quest=receipt_notice,
            text=f"Official Confirmation: Your payment of {amount} has been verified by the gym management. Your status has been updated."
        )
        
        messages.success(request, f"Payment successfully recorded. A confirmation has been sent to {target_user.username}'s log.")
        return redirect('home_url')

    context = {
        'users': all_gym_users, 
        'selected_user_id': selected_user_id,
        'today': timezone.now()
    }
    
    return render(request, 'record_payment.html', context)

TELEGRAM_BOT_TOKEN = '8906420648:AAHcpw_RXOH91wQ9XG2Tp3_B8cm65rnuoDU'
TELEGRAM_CHAT_ID = '-5141645804'

def send_telegram_notification(message_text, image_file=None):
    token = TELEGRAM_BOT_TOKEN
    chat_id = TELEGRAM_CHAT_ID

    if image_file:
        url = f"https://api.telegram.org/bot{token}/sendPhoto"
        files = {'photo': (image_file.name, image_file.read(), image_file.content_type)}
        payload = {
            'chat_id': chat_id,
            'caption': message_text,
            'parse_mode': 'Markdown',
        }
        try:
            response = requests.post(url, data=payload, files=files)
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error sending photo to Telegram: {e}")
            return None
    else:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': message_text,
            'parse_mode': 'Markdown',
        }
        try:
            response = requests.post(url, data=payload)
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error sending to Telegram: {e}")
            return None


@user_passes_test(lambda u: u.is_superuser, login_url='login_url')
def telegram_broadcast(request):
    if request.method == 'POST':
        message = request.POST.get('message', '').strip()
        image_file = request.FILES.get('image')
        if message:
            result = send_telegram_notification(message, image_file)
            if result and result.get('ok'):
                messages.success(request, 'Message broadcasted to Telegram successfully.')
            else:
                messages.error(request, 'Failed to send message to Telegram.')
        else:
            messages.error(request, 'Message cannot be empty.')
        return redirect('telegram_broadcast_url')
    return render(request, 'telegram_broadcast.html')

@login_required
def trainee_bmi(request):
    if request.user.is_superuser:
        messages.error(request, 'This section is for trainee accounts only.')
        return redirect('home_url')
    profile = UserProfile.objects.filter(user=request.user).first()
    if not profile or profile.role != UserProfile.ROLE_TRAINEE:
        messages.error(request, 'Access restricted to trainees.')
        return redirect('home_url')

    # Get trainee profile
    trainee_profile = None
    if request.user.email:
        trainee_profile = names.objects.filter(
            email__iexact=request.user.email,
            role=names.ROLE_TRAINEE
        ).first()

    if request.method == 'POST':
        # Handle planned days update
        if 'planned_days' in request.POST:
            if trainee_profile:
                progression, _ = SplitProgression.objects.get_or_create(trainee=trainee_profile)
                try:
                    planned_days = int(request.POST.get('planned_days'))
                    if 1 <= planned_days <= 7:
                        progression.planned_days_per_week = planned_days
                        progression.save()
                        messages.success(request, f'Training goal updated to {planned_days} days per week.')
                    else:
                        messages.error(request, 'Please enter a valid number between 1 and 7.')
                except (TypeError, ValueError):
                    messages.error(request, 'Please enter a valid number.')
            return redirect('trainee_bmi_url')

        # Handle BMI recording
        try:
            weight = float(request.POST.get('weight'))
            height = float(request.POST.get('height'))
            if weight <= 0 or height <= 0:
                raise ValueError
            BodyMetric.objects.create(user=request.user, weight=weight, height=height)
            messages.success(request, 'Your body metrics have been recorded.')
        except (TypeError, ValueError):
            messages.error(request, 'Please enter valid weight and height values.')
        return redirect('trainee_bmi_url')

    metrics = BodyMetric.objects.filter(user=request.user).order_by('-recorded_at')
    progress = None
    if metrics.count() >= 2:
        prev = metrics[1]
        curr = metrics[0]
        progress = {
            'weight_change': round(curr.weight - prev.weight, 1),
            'bmi_change': round(curr.bmi - prev.bmi, 1),
        }

    # Calculate training stats
    training_stats = None
    if trainee_profile:
        progression, _ = SplitProgression.objects.get_or_create(trainee=trainee_profile)
        now = timezone.now()
        week_start = now - timedelta(days=now.weekday())
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)

        # Count workouts this week
        workouts_this_week = AttendanceLog.objects.filter(
            member=trainee_profile,
            check_in__gte=week_start
        ).count()

        # Calculate completion percentage
        planned = progression.planned_days_per_week
        completion = round((workouts_this_week / planned) * 100) if planned > 0 else 0
        if completion > 100:
            completion = 100

        # Get split info
        plan = TrainingPlan.objects.filter(trainee=trainee_profile, is_active=True).first()
        current_body_part = None
        if plan and plan.split_days:
            day_index = progression.current_day_index % len(plan.split_days)
            current_body_part = plan.split_days[day_index]

        training_stats = {
            'planned_days': progression.planned_days_per_week,
            'workouts_this_week': workouts_this_week,
            'completion': completion,
            'total_workouts': progression.total_workouts_completed,
            'last_workout': progression.last_workout_date,
            'current_body_part': current_body_part,
        }

    return render(request, 'trainee_bmi.html', {
        'metrics': metrics,
        'progress': progress,
        'training_stats': training_stats,
    })


@login_required
def trainer_bmi_tracker(request):
    user_profile = UserProfile.objects.filter(user=request.user).first()
    if not user_profile or not user_profile.is_trainer:
        messages.error(request, 'Access restricted to trainers.')
        return redirect('home_url')

    assigned_trainees = names.objects.filter(trainer=request.user, role=names.ROLE_TRAINEE).order_by('-date')

    trainees_data = []
    now = timezone.now()
    week_start = now - timedelta(days=now.weekday())
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)

    for trainee in assigned_trainees:
        user_obj = None
        if trainee.email:
            user_obj = User.objects.filter(email=trainee.email).first()
        if user_obj:
            latest = BodyMetric.objects.filter(user=user_obj).order_by('-recorded_at').first()
            all_metrics = BodyMetric.objects.filter(user=user_obj).order_by('-recorded_at')
            weight_change = None
            if all_metrics.count() >= 2:
                weight_change = round(all_metrics[0].weight - all_metrics[1].weight, 1)
        else:
            latest = None
            all_metrics = []
            weight_change = None

        # Get training stats for this trainee
        training_stats = None
        progression, _ = SplitProgression.objects.get_or_create(trainee=trainee)

        # Count workouts this week
        workouts_this_week = AttendanceLog.objects.filter(
            member=trainee,
            check_in__gte=week_start
        ).count()

        # Calculate completion percentage
        planned = progression.planned_days_per_week
        completion = round((workouts_this_week / planned) * 100) if planned > 0 else 0
        if completion > 100:
            completion = 100

        # Get split info
        plan = TrainingPlan.objects.filter(trainee=trainee, is_active=True).first()
        current_body_part = None
        if plan and plan.split_days:
            day_index = progression.current_day_index % len(plan.split_days)
            current_body_part = plan.split_days[day_index]

        training_stats = {
            'planned_days': progression.planned_days_per_week,
            'workouts_this_week': workouts_this_week,
            'completion': completion,
            'total_workouts': progression.total_workouts_completed,
            'last_workout': progression.last_workout_date,
            'current_body_part': current_body_part,
        }

        trainees_data.append({
            'trainee': trainee,
            'user': user_obj,
            'latest': latest,
            'weight_change': weight_change,
            'metrics': all_metrics,
            'training_stats': training_stats,
        })

    return render(request, 'trainer_bmi_tracker.html', {'trainees_data': trainees_data})


def trainer_and_categories_list(request):
    """
    Display available trainers and training types/categories
    This is useful for selection dropdowns, directory lists, and reference pages
    """
    trainers = names.objects.filter(role=names.ROLE_TRAINER).order_by('name')
    categories = Category.objects.all().order_by('name')
    total_trainers = trainers.count()
    total_categories = categories.count()
    total_members = names.objects.filter(role=names.ROLE_TRAINEE).count()

    context = {
        'trainers': trainers,
        'categories': categories,
        'total_trainers': total_trainers,
        'total_categories': total_categories,
        'total_members': total_members,
    }

    return render(request, 'trainer_categories_list.html', context)

@login_required
def trainer_category_selector(request):
    categories = Category.objects.all().order_by('name')

    if request.method == 'POST':
        preferred_id = request.POST.get('preferred_trainer')
        if preferred_id:
            trainee_profile = names.objects.filter(
                email=request.user.email,
                role=names.ROLE_TRAINEE,
            ).first()
            if trainee_profile:
                try:
                    preferred = User.objects.get(
                        id=int(preferred_id),
                        profile__role=UserProfile.ROLE_TRAINER,
                    )
                    trainee_profile.preferred_trainer = preferred
                    trainee_profile.save()
                    messages.success(request, f"Preferred trainer set to {preferred.username}")
                except (User.DoesNotExist, ValueError):
                    messages.error(request, "Invalid trainer selected.")
            else:
                messages.error(request, "No trainee profile found.")
        else:
            messages.error(request, "No trainer selected.")
        return redirect('trainer_selector_url')

    trainers = names.objects.filter(role=names.ROLE_TRAINER).select_related('category').order_by('name')

    current_preferred = None
    if request.user.is_authenticated:
        trainee = names.objects.filter(
            email=request.user.email,
            role=names.ROLE_TRAINEE,
        ).first()
        if trainee and trainee.preferred_trainer_id:
            current_preferred = trainee.preferred_trainer

    context = {
        'trainers': trainers,
        'categories': categories,
        'current_preferred': current_preferred,
    }

    return render(request, 'trainer_category_selector.html', context)

@require_http_methods(["GET"])
def trainer_and_categories_api(request):
    """
    JSON API endpoint for getting trainers and categories
    Useful for AJAX requests or external integrations
    
    Usage: /api/trainers-categories/
    
    Returns:
    {
        "trainers": [
            {
                "id": 1,
                "name": "John Doe",
                "email": "john@example.com",
                "category": "Strength Training",
                "date_created": "2024-01-15"
            }
        ],
        "categories": [
            {
                "id": 1,
                "name": "Strength Training",
                "members_count": 10
            }
        ],
        "stats": {
            "total_trainers": 3,
            "total_categories": 5,
            "total_members": 25
        }
    }
    """
    trainers = names.objects.filter(role=names.ROLE_TRAINER).order_by('name')
    categories = Category.objects.all()

    trainers_data = []
    for trainer in trainers:
        trainers_data.append({
            'id': trainer.id,
            'name': trainer.name,
            'email': trainer.email,
            'phone_number': trainer.phone_number,
            'category': trainer.category.name if trainer.category else None,
            'date_created': trainer.date.isoformat() if trainer.date else None,
        })
    
    # Build category data
    categories_data = []
    for category in categories:
        categories_data.append({
            'id': category.id,
            'name': category.name,
            'members_count': category.names_set.count(),
        })
    
    # Build response
    response_data = {
        'trainers': trainers_data,
        'categories': categories_data,
        'stats': {
            'total_trainers': trainers.count(),
            'total_categories': categories.count(),
            'total_members': names.objects.filter(role=names.ROLE_TRAINEE).count(),
        }
    }
    
    return JsonResponse(response_data)

@login_required
def create_session(request):
    # Fetch trainer's names profile and UserProfile
    trainer_names_profile = None
    trainer_user_profile = None
    if request.user.is_authenticated:
        trainer_names_profile = names.objects.filter(email=request.user.email, role='trainer').first()
        trainer_user_profile = UserProfile.objects.filter(user=request.user).first()

    if request.method == 'POST':
        # 1. Securely fetch the trainer profile using the logged-in user's email
        if not trainer_names_profile:
            messages.error(request, "Access denied. Trainer profile not found for this account.")
            return redirect('home_url')

        # 2. Extract form data from the homepage modal submission
        title = request.POST.get('title')
        description = request.POST.get('description')
        session_date_raw = request.POST.get('session_date')
        max_trainees = request.POST.get('max_trainees')
        space_id = request.POST.get('space')
        duration_minutes = request.POST.get('duration_minutes', 60)

        # Validation checks
        if not title or not session_date_raw:
            messages.error(request, "Session title and date/time are required fields.")
            return redirect('create_session_url')

        try:
            from datetime import timedelta
            from django.utils import timezone
            session_start = timezone.make_aware(timezone.datetime.fromisoformat(session_date_raw))
            session_end = session_start + timedelta(minutes=int(duration_minutes))

            # If a space is selected, check availability
            selected_space = None
            if space_id:
                try:
                    selected_space = TrainingSpace.objects.get(id=space_id)
                except TrainingSpace.DoesNotExist:
                    messages.error(request, "Selected training space not found.")
                    return redirect('create_session_url')

                if selected_space.is_under_maintenance:
                    messages.error(request, f'"{selected_space.name}" is currently under maintenance and unavailable for booking. Please choose a different space.')
                    return redirect('create_session_url')

                # Check for overlapping bookings
                overlapping = TrainingSession.objects.filter(space=selected_space)
                for existing in overlapping:
                    existing_end = existing.session_date + timedelta(minutes=existing.duration_minutes)
                    if existing.session_date < session_end and existing_end > session_start:
                        messages.error(request, f"This space is already booked from {existing.session_date.strftime('%I:%M %p')} to {existing_end.strftime('%I:%M %p')}. Please choose a different time or space.")
                        return redirect('create_session_url')

            # 3. Instantiate and build the training session item matrix
            new_session = TrainingSession(
                title=title,
                description=description,
                session_date=session_date_raw,
                max_trainees=max_trainees,
                trainer=trainer_names_profile,
                space=selected_space,
                duration_minutes=duration_minutes,
            )
            new_session.save()
            
            # 4. Notify all trainees assigned to this trainer about the new session
            assigned_trainees = names.objects.filter(trainer=request.user, role=names.ROLE_TRAINEE)
            registration_url = request.build_absolute_uri(reverse('register_session_url', args=[new_session.id]))
            
            for trainee in assigned_trainees:
                trainee_user = None
                if trainee.email:
                    trainee_user = User.objects.filter(email__iexact=trainee.email).first()
                
                if not trainee_user:
                    continue
                
                notification_question = questions.objects.create(
                    name=trainee_user.username,
                    email=trainee.email or trainee_user.email,
                    quest=f'New training session: {title}'
                )
                space_info = f"\nLocation: {selected_space.name}" if selected_space else ""
                message_text = f'''Your trainer has created a new session: "{title}"

Session details: {description or "No description provided"}
{space_info}
Date: {session_start.strftime('%B %d, %Y at %I:%M %p')}

Register for this session:
{registration_url}'''
                
                response_model.objects.create(
                    name=request.user,
                    quest=notification_question,
                    text=message_text,
                    is_read=False
                )
            
            messages.success(request, f"Successfully broadcasted live training session: '{title}'! Notifications sent to {assigned_trainees.count()} trainee(s).")
            
        except Exception as e:
            messages.error(request, f"Error creating session: {str(e)}")
            
        return redirect('session_hub_url')

    # GET - show spaces matching the trainer's category (excluding maintenance spaces)
    spaces = TrainingSpace.objects.none()
    if trainer_user_profile and trainer_user_profile.category:
        spaces = TrainingSpace.objects.filter(category=trainer_user_profile.category, is_under_maintenance=False).select_related('category')
    else:
        spaces = TrainingSpace.objects.filter(is_under_maintenance=False).select_related('category')

    # Count maintenance spaces for info message
    maintenance_count = TrainingSpace.objects.filter(is_under_maintenance=True).count()

    return render(request, 'session_create.html', {
        'spaces': spaces,
        'maintenance_count': maintenance_count,
    })

@login_required
def register_session(request, session_id):
    """
    Enables a trainee to book a slot for their assigned coach's session,
    unless the specified capacity cap has been hit.
    """
    session = get_object_or_404(TrainingSession, id=session_id)
    
    # Find the trainee record - match by user's email or by trainer assignment
    trainee_profile = None
    if request.user.email:
        trainee_profile = names.objects.filter(
            email__iexact=request.user.email, 
            role=names.ROLE_TRAINEE
        ).first()
    
    if not trainee_profile:
        # Try to find by trainer assignment
        trainee_profile = names.objects.filter(
            trainer=request.user,
            role=names.ROLE_TRAINEE
        ).first()
    
    if not trainee_profile:
        messages.error(request, "Only active trainees can register for sessions.")
        return redirect('home_url')

    # Ensure this trainee is assigned to this trainer
    # trainee_profile.trainer is a User; session.trainer is a names object; compare via User
    if trainee_profile.trainer != session.trainer.trainer:
        messages.error(request, "Access Denied: You cannot register for sessions outside your assigned trainer's track.")
        return redirect('home_url')

    # Determine registration status for this trainee
    already_registered = session.registered_trainees.filter(id=trainee_profile.id).exists()

    if request.method == 'POST':
        action = request.POST.get('action', 'register')

        if action == 'unregister':
            if already_registered:
                session.registered_trainees.remove(trainee_profile)
                messages.success(request, f"Your registration for '{session.title}' has been cancelled.")
            else:
                messages.warning(request, "You are not registered for this session.")
            return redirect('trainee_sessions_url')

        if action == 'register':
            if already_registered:
                messages.warning(request, "You are already registered for this session.")
                return redirect('trainee_sessions_url')

            if session.is_full:
                messages.error(request, "Registration Closed: The maximum trainee capacity for this session has been reached.")
                return redirect('trainee_sessions_url')

            session.registered_trainees.add(trainee_profile)
            messages.success(request, f"Success! You have claimed a spot for '{session.title}'.")
            return redirect('trainee_sessions_url')

    # GET request - show session details and confirmation form
    context = {
        'session': session,
        'trainee': trainee_profile,
        'slots_available': session.slots_left,
        'total_registered': session.registered_trainees.count(),
        'already_registered': already_registered,
    }
    return render(request, 'session_register.html', context)


@login_required
def session_hub(request):
    user_profile = UserProfile.objects.filter(user=request.user).first()
    if not user_profile or not user_profile.is_trainer:
        messages.error(request, "Access restricted to trainers only.")
        return redirect('home_url')

    return render(request, 'session_hub.html')


@login_required
def trainee_session_list(request):
    if request.user.is_superuser:
        messages.error(request, 'This page is for trainees only.')
        return redirect('home_url')

    trainee_profile = None
    if request.user.email:
        trainee_profile = names.objects.filter(
            email__iexact=request.user.email,
            role=names.ROLE_TRAINEE
        ).first()

    if not trainee_profile:
        messages.error(request, 'Trainee profile not found for your account.')
        return redirect('home_url')

    trainer_user = trainee_profile.trainer
    if not trainer_user:
        messages.error(request, 'You are not currently assigned to a trainer.')
        return redirect('home_url')

    trainer_profile = names.objects.filter(
        email__iexact=trainer_user.email,
        role=names.ROLE_TRAINER
    ).first()
    if not trainer_profile:
        messages.error(request, 'Trainer profile could not be found for your assigned coach.')
        return redirect('home_url')

    sessions = TrainingSession.objects.filter(trainer=trainer_profile, session_date__gte=timezone.now()).order_by('session_date')
    registered_session_ids = set(
        session_id for session_id in trainee_profile.registered_sessions.values_list('id', flat=True)
    )

    session_rows = []
    for session in sessions:
        session_rows.append({
            'session': session,
            'already_registered': session.id in registered_session_ids,
            'can_register': (not session.is_full) and (session.id not in registered_session_ids),
        })

    # Get split progression info
    split_info = None
    progression, _ = SplitProgression.objects.get_or_create(trainee=trainee_profile)
    plan = TrainingPlan.objects.filter(trainee=trainee_profile, is_active=True).first()

    # Fall back to most recent plan if no active plan
    if not plan:
        plan = TrainingPlan.objects.filter(trainee=trainee_profile).order_by('-created_at').first()

    if plan and plan.split_days:
        day_index = progression.current_day_index % len(plan.split_days)
        split_info = {
            'plan': plan,
            'progression': progression,
            'current_body_part': plan.split_days[day_index],
            'split_type_display': plan.get_split_type_display(),
            'total_days': len(plan.split_days),
            'current_day_number': day_index + 1,
        }

    return render(request, 'session_list.html', {
        'trainer': trainer_user,
        'sessions': session_rows,
        'trainee': trainee_profile,
        'split_info': split_info,
    })


@user_passes_test(lambda u: u.is_superuser, login_url='login_url')
def training_space_list(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        category_id = request.POST.get('category')
        description = request.POST.get('description')
        if name and category_id:
            TrainingSpace.objects.create(name=name, category_id=category_id, description=description)
            messages.success(request, f'Training space "{name}" created.')
            return redirect('training_space_list_url')
    spaces = TrainingSpace.objects.select_related('category').all()
    categories = Category.objects.all()
    return render(request, 'training_space_list.html', {'spaces': spaces, 'categories': categories})

@user_passes_test(lambda u: u.is_superuser, login_url='login_url')
def training_space_edit(request, space_id):
    space = get_object_or_404(TrainingSpace, id=space_id)
    if request.method == 'POST':
        name = request.POST.get('name')
        category_id = request.POST.get('category')
        description = request.POST.get('description')
        is_under_maintenance = request.POST.get('is_under_maintenance') == '1'
        if name and category_id:
            space.name = name
            space.category_id = category_id
            space.description = description
            space.is_under_maintenance = is_under_maintenance
            space.save()
            messages.success(request, f'Training space "{name}" updated.')
            return redirect('training_space_list_url')
    categories = Category.objects.all()
    return render(request, 'training_space_edit.html', {'space': space, 'categories': categories})

@user_passes_test(lambda u: u.is_superuser, login_url='login_url')
def training_space_toggle_maintenance(request, space_id):
    space = get_object_or_404(TrainingSpace, id=space_id)
    space.is_under_maintenance = not space.is_under_maintenance
    space.save()
    status = "under maintenance" if space.is_under_maintenance else "available"
    messages.success(request, f'Training space "{space.name}" is now {status}.')
    return redirect('training_space_list_url')

@user_passes_test(lambda u: u.is_superuser, login_url='login_url')
def training_space_delete(request, space_id):
    space = get_object_or_404(TrainingSpace, id=space_id)
    space.delete()
    messages.success(request, 'Training space deleted.')
    return redirect('training_space_list_url')


@require_http_methods(["GET"])
def api_available_spaces(request):
    """
    Returns spaces that are available for a given datetime range.
    Query params: date (ISO datetime), duration_minutes (default 60), space_id (optional filter)
    """
    import json
    from datetime import timedelta
    from django.utils import timezone

    date_str = request.GET.get('date')
    duration = int(request.GET.get('duration_minutes', 60))
    space_id = request.GET.get('space_id')

    if not date_str:
        return JsonResponse({'error': 'date parameter is required'}, status=400)

    try:
        session_start = timezone.make_aware(timezone.datetime.fromisoformat(date_str))
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid date format. Use ISO format.'}, status=400)

    session_end = session_start + timedelta(minutes=duration)

    spaces_qs = TrainingSpace.objects.select_related('category').filter(is_under_maintenance=False)

    available = []
    for space in spaces_qs:
        existing_sessions = TrainingSession.objects.filter(space=space)
        has_overlap = False
        for existing in existing_sessions:
            existing_end = existing.session_date + timedelta(minutes=existing.duration_minutes)
            if existing.session_date < session_end and existing_end > session_start:
                has_overlap = True
                break
        if not has_overlap:
            available.append({
                'id': space.id,
                'name': space.name,
                'category_name': space.category.name,
                'category_id': space.category_id,
            })

    return JsonResponse({'spaces': available})


# ─── ID Card ───────────────────────────────────────────────────────────────────

def generate_qr_image(member_id_obj):
    import qrcode
    from qrcode.constants import ERROR_CORRECT_H
    from io import BytesIO
    from django.core.files.base import ContentFile

    qr = qrcode.QRCode(box_size=14, border=4, error_correction=ERROR_CORRECT_H)
    qr.add_data(member_id_obj.unique_id)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    filename = f"qr_{member_id_obj.unique_id[:16]}.png"
    member_id_obj.qr_code.save(filename, ContentFile(buffer.getvalue()), save=False)
    member_id_obj.save()


def qr_data_uri(member_id_obj):
    import qrcode
    from qrcode.constants import ERROR_CORRECT_H
    from io import BytesIO
    import base64

    qr = qrcode.QRCode(box_size=14, border=4, error_correction=ERROR_CORRECT_H)
    qr.add_data(member_id_obj.unique_id)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    b64 = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{b64}"


def _get_names_profile(user):
    """Match a names record to a User via email, or auto-create one."""
    if not user or not user.is_authenticated:
        return None
    person = names.objects.filter(email__iexact=user.email).first()
    if person:
        return person
    from .models import UserProfile
    profile = UserProfile.objects.filter(user=user).first()
    role = profile.role if profile and hasattr(profile, 'role') else 'trainee'
    display_name = user.get_full_name() or user.username
    person = names.objects.create(
        name=display_name,
        email=user.email or '',
        role=role,
    )
    return person


@login_required
def my_id_card(request):
    person = _get_names_profile(request.user)
    if not person or person.role not in ('trainer', 'trainee'):
        messages.error(request, "ID cards are only available for trainers and trainees.")
        return redirect('home_url')

    mid, created = MemberID.objects.get_or_create(member=person)
    if created or not mid.unique_id:
        mid.unique_id = str(uuid.uuid4())
        mid.save()
        generate_qr_image(mid)

    qr_uri = qr_data_uri(mid)
    return render(request, 'my_id_card.html', {'mid': mid, 'person': person, 'qr_uri': qr_uri})


@login_required
def regenerate_qr(request):
    person = _get_names_profile(request.user)
    if not person or person.role not in ('trainer', 'trainee'):
        messages.error(request, "ID cards are only available for trainers and trainees.")
        return redirect('home_url')
    mid = MemberID.objects.get(member=person)
    if not mid.unique_id:
        mid.unique_id = str(uuid.uuid4())
        mid.save()
    generate_qr_image(mid)
    messages.success(request, "QR code regenerated — use this new code for printing.")
    return redirect('my_id_card_url')


@login_required
def generate_all_missing_ids(request):
    if not request.user.is_superuser:
        messages.error(request, "Admin only.")
        return redirect('home_url')
    count = 0
    for person in names.objects.all():
        mid, created = MemberID.objects.get_or_create(member=person)
        needs_uuid = created or not mid.unique_id
        if needs_uuid:
            mid.unique_id = str(uuid.uuid4())
        if needs_uuid or not mid.qr_code:
            generate_qr_image(mid)
            count += 1
    messages.success(request, f"Generated {count} ID card(s). All members now have IDs.")
    return redirect('admin_scan_qr')


@login_required
def regenerate_all_qr_codes(request):
    if not request.user.is_superuser:
        messages.error(request, "Admin only.")
        return redirect('home_url')
    count = 0
    for person in names.objects.all():
        mid, created = MemberID.objects.get_or_create(member=person)
        if not mid.unique_id:
            mid.unique_id = str(uuid.uuid4())
            mid.save()
        generate_qr_image(mid)
        count += 1
    messages.success(request, f"Regenerated QR codes for {count} member(s). UUIDs were NOT changed.")
    return redirect('admin_scan_qr')


@login_required
def id_card_pdf(request):
    person = _get_names_profile(request.user)
    if not person or person.role not in ('trainer', 'trainee'):
        messages.error(request, "ID cards are only available for trainers and trainees.")
        return redirect('home_url')

    mid, created = MemberID.objects.get_or_create(member=person)
    if created or not mid.unique_id:
        mid.unique_id = str(uuid.uuid4())
        mid.save()
        generate_qr_image(mid)

    qr_uri = qr_data_uri(mid)
    return render(request, 'id_card_pdf.html', {'mid': mid, 'person': person, 'qr_uri': qr_uri})


def _has_active_membership(member_profile):
    if not member_profile or member_profile.role != 'trainee':
        return True
    if not member_profile.email:
        return False
    user = User.objects.filter(email__iexact=member_profile.email).first()
    if not user:
        return False
    from datetime import date
    today = date.today()
    return MembershipPayment.objects.filter(
        user=user,
        is_verified=True,
        subscription_end__gte=today
    ).exists()


# ─── QR Scanner (Admin) ────────────────────────────────────────────────────────

@user_passes_test(lambda u: u.is_superuser)
def admin_scan_qr(request):
    return render(request, 'admin_scan_qr.html')


def admin_scan_checkin(request):
    attendance = AttendanceLog.objects.select_related('member', 'checked_in_by').order_by('-check_in')[:50]
    return render(request, 'admin_scan_checkin.html', {'attendance': attendance})


def admin_scan_checkout(request):
    return render(request, 'admin_scan_checkout.html')


@login_required
@require_http_methods(["POST"])
def record_attendance(request):
    import json
    from datetime import datetime
    data = json.loads(request.body)
    unique_id = data.get('unique_id', '').strip()

    if not unique_id:
        return JsonResponse({'ok': False, 'error': 'No ID provided'}, status=400)

    try:
        mid = MemberID.objects.get(unique_id=unique_id)
    except MemberID.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Unknown ID card', 'debug': {'received': unique_id, 'len': len(unique_id), 'chars': [ord(c) for c in unique_id[:50]]}}, status=404)

    # Find today's active check-in for this member
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow_start = today_start + timezone.timedelta(days=1)
    active = AttendanceLog.objects.filter(
        member=mid.member,
        check_in__gte=today_start,
        check_in__lt=tomorrow_start,
        check_out__isnull=True
    ).first()

    if active is not None:
        active.check_out = timezone.now()
        active.checked_out_by = request.user if request.user.is_authenticated else None
        active.save(update_fields=['check_out', 'checked_out_by'])

        if mid.member.role == 'trainee':
            from .models import SplitProgression, TrainingPlan
            progression, created = SplitProgression.objects.get_or_create(trainee=mid.member)
            plan = TrainingPlan.objects.filter(trainee=mid.member, is_active=True).first()
            if plan and plan.split_days:
                if progression.last_workout_date != today_start.date():
                    progression.advance_to_next_day()

        return JsonResponse({
            'ok': True,
            'action': 'checkout',
            'member_name': mid.member.name,
            'role': mid.member.role,
            'check_in': timezone.localtime(active.check_in).strftime('%H:%M'),
            'check_out': timezone.localtime(active.check_out).strftime('%H:%M'),
        })

    if not _has_active_membership(mid.member):
        return JsonResponse({'ok': False, 'error': f'{mid.member.name} does not have an active membership. Please pay to check in.'}, status=403)

    attendance = AttendanceLog.objects.create(
        member=mid.member,
        checked_in_by=request.user if request.user.is_authenticated else None,
    )

    return JsonResponse({
        'ok': True,
        'action': 'checkin',
        'member_name': mid.member.name,
        'role': mid.member.role,
        'time': timezone.localtime(attendance.check_in).strftime('%Y-%m-%d %H:%M'),
    })


@login_required
@require_http_methods(["POST"])
def scan_entry(request):
    import json
    data = json.loads(request.body)
    unique_id = data.get('unique_id', '').strip()
    session_id = data.get('session_id')

    if not unique_id:
        return JsonResponse({'ok': False, 'error': 'No ID provided'}, status=400)

    try:
        mid = MemberID.objects.get(unique_id=unique_id)
    except MemberID.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Unknown ID card', 'debug': {'received': unique_id, 'len': len(unique_id), 'chars': [ord(c) for c in unique_id[:50]]}}, status=404)

    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow_start = today_start + timezone.timedelta(days=1)
    active = AttendanceLog.objects.filter(
        member=mid.member,
        check_in__gte=today_start,
        check_in__lt=tomorrow_start,
        check_out__isnull=True
    ).first()
    if active:
        active.check_out = timezone.now()
        active.checked_out_by = request.user if request.user.is_authenticated else None
        active.save(update_fields=['check_out', 'checked_out_by'])

        if mid.member.role == 'trainee':
            from .models import SplitProgression, TrainingPlan
            progression, created = SplitProgression.objects.get_or_create(trainee=mid.member)
            plan = TrainingPlan.objects.filter(trainee=mid.member, is_active=True).first()
            if plan and plan.split_days:
                if progression.last_workout_date != today_start.date():
                    progression.advance_to_next_day()

        return JsonResponse({
            'ok': True,
            'action': 'checkout',
            'member_name': mid.member.name,
            'role': mid.member.role,
            'check_in': timezone.localtime(active.check_in).strftime('%H:%M'),
            'check_out': timezone.localtime(active.check_out).strftime('%H:%M'),
        })

    if not _has_active_membership(mid.member):
        return JsonResponse({'ok': False, 'error': f'{mid.member.name} does not have an active membership. Please pay to check in.'}, status=403)

    session = None
    if session_id:
        try:
            session = TrainingSession.objects.get(id=session_id)
        except TrainingSession.DoesNotExist:
            pass

    attendance = AttendanceLog.objects.create(
        member=mid.member,
        session=session,
        checked_in_by=request.user if request.user.is_authenticated else None,
    )

    return JsonResponse({
        'ok': True,
        'action': 'checkin',
        'member_name': mid.member.name,
        'role': mid.member.role,
        'time': timezone.localtime(attendance.check_in).strftime('%Y-%m-%d %H:%M'),
        'session': session.title if session else None,
    })


@login_required
@require_http_methods(["POST"])
def check_out_entry(request):
    import json
    data = json.loads(request.body)
    unique_id = data.get('unique_id', '').strip()

    if not unique_id:
        return JsonResponse({'ok': False, 'error': 'No ID provided'}, status=400)

    try:
        mid = MemberID.objects.get(unique_id=unique_id)
    except MemberID.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Unknown ID card', 'debug': {'received': unique_id, 'len': len(unique_id), 'chars': [ord(c) for c in unique_id[:50]]}}, status=404)

    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow_start = today_start + timezone.timedelta(days=1)

    attendance = AttendanceLog.objects.filter(
        member=mid.member,
        check_in__gte=today_start,
        check_in__lt=tomorrow_start,
        check_out__isnull=True
    ).first()

    if not attendance:
        return JsonResponse({'ok': False, 'error': 'No active check-in found for today'}, status=404)

    attendance.check_out = timezone.now()
    attendance.checked_out_by = request.user if request.user.is_authenticated else None
    attendance.save(update_fields=['check_out', 'checked_out_by'])

    if mid.member.role == 'trainee':
        from .models import SplitProgression, TrainingPlan
        progression, created = SplitProgression.objects.get_or_create(trainee=mid.member)
        plan = TrainingPlan.objects.filter(trainee=mid.member, is_active=True).first()
        if plan and plan.split_days:
            if progression.last_workout_date != today_start.date():
                progression.advance_to_next_day()

    return JsonResponse({
        'ok': True,
        'member_name': mid.member.name,
        'role': mid.member.role,
        'check_in': timezone.localtime(attendance.check_in).strftime('%Y-%m-%d %H:%M'),
        'check_out': timezone.localtime(attendance.check_out).strftime('%Y-%m-%d %H:%M'),
    })


@login_required
@require_http_methods(["POST"])
def check_in_entry(request):
    import json
    data = json.loads(request.body)
    unique_id = data.get('unique_id', '').strip()

    if not unique_id:
        return JsonResponse({'ok': False, 'error': 'No ID provided'}, status=400)
    try:
        mid = MemberID.objects.get(unique_id=unique_id)
    except MemberID.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Unknown ID card', 'debug': {'received': unique_id, 'len': len(unique_id), 'chars': [ord(c) for c in unique_id[:50]]}}, status=404)

    if not _has_active_membership(mid.member):
        return JsonResponse({'ok': False, 'error': f'{mid.member.name} does not have an active membership. Please pay to check in.'}, status=403)

    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow_start = today_start + timezone.timedelta(days=1)

    active = AttendanceLog.objects.filter(
        member=mid.member,
        check_in__gte=today_start,
        check_in__lt=tomorrow_start,
        check_out__isnull=True
    ).first()

    if active is not None:
        return JsonResponse({
            'ok': False,
            'error': f'{mid.member.name} is already checked in since {timezone.localtime(active.check_in).strftime("%H:%M")}'
        }, status=409)

    attendance = AttendanceLog.objects.create(
        member=mid.member,
        checked_in_by=request.user if request.user.is_authenticated else None,
    )

    return JsonResponse({
        'ok': True,
        'action': 'checkin',
        'member_name': mid.member.name,
        'role': mid.member.role,
        'time': timezone.localtime(attendance.check_in).strftime('%Y-%m-%d %H:%M'),
    })


# ─── Attendance Log Page ───────────────────────────────────────────────────────

@user_passes_test(lambda u: u.is_superuser)
def attendance_dashboard(request):
    from django.db.models import Count
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = today_start - timezone.timedelta(days=7)
    month_ago = today_start - timezone.timedelta(days=30)

    def stats_since(since):
        logs = AttendanceLog.objects.filter(check_in__gte=since).select_related('member')
        total = logs.count()
        by_gender = logs.values_list('member__gender', flat=True)
        male = sum(1 for g in by_gender if g == 'male')
        female = sum(1 for g in by_gender if g == 'female')
        by_category = (
            logs.values('member__category__name')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        return {
            'total': total,
            'male': male,
            'female': female,
            'by_category': by_category,
        }

    daily = stats_since(today_start)
    weekly = stats_since(week_ago)
    monthly = stats_since(month_ago)

    periods = [
        ('Today', daily),
        ('This Week (7 days)', weekly),
        ('This Month (30 days)', monthly),
    ]

    return render(request, 'attendance_dashboard.html', {
        'periods': periods,
    })


@login_required
def attendance_log_view(request):
    person = _get_names_profile(request.user)
    if not person:
        messages.error(request, "Profile not found.")
        return redirect('home_url')

    if request.user.is_superuser:
        logs = AttendanceLog.objects.select_related('member', 'checked_in_by').order_by('-check_in')[:200]
    elif person.role == 'trainer':
        logs = AttendanceLog.objects.filter(member__trainer=person).select_related('member').order_by('-check_in')[:200]
    else:
        logs = AttendanceLog.objects.filter(member=person).select_related('member').order_by('-check_in')[:200]

    return render(request, 'attendance_log.html', {'logs': logs})


@login_required
def trainer_currently_in(request):
    person = _get_names_profile(request.user)
    if not person or person.role != 'trainer':
        messages.error(request, "Only trainers can access this page.")
        return redirect('home_url')
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    # Get all trainees who checked in today (both currently in and already left)
    today_logs = AttendanceLog.objects.filter(
        check_in__gte=today_start,
        member__trainer=request.user
    ).select_related('member', 'member__category').order_by('-check_in')
    
    # Separate into currently in and already left
    currently_in = []
    already_left = []
    seen_members = set()
    
    for log in today_logs:
        if log.member_id in seen_members:
            continue
        seen_members.add(log.member_id)
        if log.check_out is None:
            currently_in.append(log)
        else:
            already_left.append(log)
    
    return render(request, 'trainer_currently_in.html', {
        'currently_in': currently_in,
        'already_left': already_left,
        'total_currently_in': len(currently_in),
        'total_today': len(currently_in) + len(already_left),
    })


# ═══════════════════════════════════════════════════════════════════════════════
# REGISTRAR ROLE
# ═══════════════════════════════════════════════════════════════════════════════

def _require_registrar(view_func):
    @login_required(login_url='login_url')
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        profile = UserProfile.objects.filter(user=request.user).first()
        if not profile or profile.role != UserProfile.ROLE_REGISTRAR:
            messages.error(request, 'Access restricted to registrars.')
            return redirect('home_url')
        request.registrar_profile = profile
        return view_func(request, *args, **kwargs)
    return wrapper


@_require_registrar
def registrar_dashboard(request):
    from django.db.models import Count
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # People checked in today (currently in the gym)
    today_logs = AttendanceLog.objects.filter(check_in__gte=today_start, check_out__isnull=True).select_related('member', 'member__category')

    total_today = today_logs.count()

    # Crowdedness by category
    by_category = (
        today_logs.values('member__category__name')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    # Active trainers - trainers who have attendance records today
    active_trainer_ids = today_logs.filter(member__role='trainer').values_list('member_id', flat=True).distinct()
    active_trainers = names.objects.filter(id__in=active_trainer_ids)

    # Recent check-ins
    recent = today_logs.order_by('-check_in')[:30]

    all_categories = Category.objects.all()

    return render(request, 'registrar_dashboard.html', {
        'total_today': total_today,
        'by_category': by_category,
        'active_trainers': active_trainers,
        'recent': recent,
        'all_categories': all_categories,
    })


@_require_registrar
def registrar_register(request):
    all_categories = Category.objects.all()

    if request.method == 'POST':
        name = request.POST.get('full_name')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        detail = request.POST.get('detail')
        gender = request.POST.get('gender')
        category_id = request.POST.get('category')
        image = request.FILES.get('profile_image')

        # Only trainees can be registered by registrar
        role = names.ROLE_TRAINEE

        if email:
            email_lower = email.strip().lower()
            if User.objects.filter(email__iexact=email_lower).exists():
                messages.error(request, 'A user with this email address already exists.')
                return render(request, 'registrar_register.html', {'categories': all_categories})
            if names.objects.filter(email__iexact=email_lower).exists():
                messages.error(request, 'A member with this email address already exists.')
                return render(request, 'registrar_register.html', {'categories': all_categories})

        if phone_number:
            try:
                ethiopian_phone_validator(phone_number)
            except Exception:
                messages.error(request, 'Phone number must be valid Ethiopian format (e.g. +251912345678 or 0912345678).')
                return render(request, 'registrar_register.html', {'categories': all_categories})
            if names.objects.filter(phone_number=phone_number).exists():
                messages.error(request, 'A member with this phone number already exists.')
                return render(request, 'registrar_register.html', {'categories': all_categories})

        username_base = name.lower().replace(' ', '').replace('-', '')[:15]
        username = username_base
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{username_base}{counter}"
            counter += 1

        password = ''.join(secrets.choice(string.digits) for _ in range(8))

        try:
            user = User.objects.create_user(username=username, email=email, password=password)
            user.first_name = name.split()[0] if ' ' in name else name
            user.last_name = ' '.join(name.split()[1:]) if ' ' in name else ''
            user.save()

            UserProfile.objects.get_or_create(
                user=user,
                defaults={'role': role, 'gender': gender, 'category_id': category_id}
            )
        except Exception as e:
            messages.error(request, f"Error creating account: {str(e)}")
            return render(request, 'registrar_register.html', {'categories': all_categories})

        names.objects.create(
            name=name,
            email=email,
            phone_number=phone_number,
            detail=detail,
            gender=gender,
            role=role,
            category_id=category_id,
            image=image,
        )

        subject = "Welcome to Future Gym - Your Account Details"
        message = f"""Dear {name},

Welcome to Future Gym! Your account has been created.

Username: {username}
Password: {password}
Email: {email}

Please log in and change your password immediately.

Best regards,
Future Gym Management"""
        send_email_async(subject, message, [email])

        messages.success(request, f'Trainee "{name}" registered successfully! Username: {username}, Password: {password}')
        return redirect('registrar_dashboard_url')

    return render(request, 'registrar_register.html', {'categories': all_categories})


@_require_registrar
def registrar_scan_qr(request):
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    attendance = AttendanceLog.objects.filter(
        check_in__gte=today_start, check_out__isnull=True
    ).select_related('member', 'checked_in_by').order_by('-check_in')[:50]
    return render(request, 'registrar_scan_qr.html', {'attendance': attendance})


@_require_registrar
def registrar_scan_checkout(request):
    return render(request, 'registrar_scan_checkout.html')


@_require_registrar
def registrar_attendance_log(request):
    logs = AttendanceLog.objects.select_related('member', 'checked_in_by').order_by('-check_in')[:200]
    return render(request, 'attendance_log.html', {'logs': logs})


@_require_registrar
def registrar_currently_in(request):
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_logs = AttendanceLog.objects.filter(
        check_in__gte=today_start,
        check_out__isnull=True
    ).select_related('member', 'member__category', 'checked_in_by').order_by('-check_in')
    members_in = {}
    for log in today_logs:
        mid = log.member_id
        if mid not in members_in:
            members_in[mid] = log
    currently_in = list(members_in.values())
    total = len(currently_in)
    return render(request, 'registrar_currently_in.html', {
        'currently_in': currently_in,
        'total': total,
    })


@login_required
def rate_trainer(request, trainer_name):
    trainer = get_object_or_404(names, name=trainer_name, role=names.ROLE_TRAINER)
    trainee = names.objects.filter(email=request.user.email, role=names.ROLE_TRAINEE).first()
    if not trainee or trainee.trainer != request.user:
        messages.error(request, 'You can only rate your assigned trainer.')
        return redirect('detail_url', name=trainer_name)

    existing = TrainerRating.objects.filter(trainee=trainee, trainer=trainer).first()
    if request.method == 'POST':
        rating_val = request.POST.get('rating')
        comment = request.POST.get('comment', '').strip()
        if not rating_val or not rating_val.isdigit() or int(rating_val) not in range(6):
            messages.error(request, 'Please select a valid rating between 0 and 5.')
            return redirect('rate_trainer_url', trainer_name=trainer_name)
        if existing:
            existing.rating = int(rating_val)
            existing.comment = comment
            existing.save()
            messages.success(request, f'Your rating for {trainer.name} has been updated.')
        else:
            TrainerRating.objects.create(
                trainee=trainee, trainer=trainer,
                rating=int(rating_val), comment=comment
            )
            messages.success(request, f'Thank you! You rated {trainer.name} {rating_val}/5.')
        return redirect('detail_url', name=trainer_name)

    return render(request, 'rate_trainer.html', {
        'trainer': trainer,
        'existing': existing,
    })


@user_passes_test(lambda u: u.is_superuser, login_url='login_url')
def trainer_ratings_dashboard(request):
    trainers = names.objects.filter(role=names.ROLE_TRAINER).annotate(
        avg_rating=Avg('ratings_received__rating'),
        rating_count=Count('ratings_received')
    ).order_by('-avg_rating')

    return render(request, 'trainer_ratings.html', {
        'trainers': trainers,
    })


@login_required
def trainer_my_feedback(request):
    if not (hasattr(request.user, 'profile') and request.user.profile.is_trainer):
        messages.error(request, 'Only trainers can view this page.')
        return redirect('home_url')
    trainer_names = names.objects.filter(email=request.user.email, role=names.ROLE_TRAINER).first()
    if not trainer_names:
        messages.error(request, 'Trainer profile not found.')
        return redirect('home_url')
    ratings = TrainerRating.objects.filter(trainer=trainer_names).select_related('trainee').order_by('-created_at')
    stats = ratings.aggregate(avg_rating=Avg('rating'), count=Count('id'))
    return render(request, 'trainer_my_feedback.html', {
        'ratings': ratings,
        'stats': stats,
        'trainer': trainer_names,
    })


from datetime import date, timedelta


def _notify_trainee_plan_update(trainer_user, trainee, plan, action_label):
    trainee_user = None
    if trainee.email:
        trainee_user = User.objects.filter(email__iexact=trainee.email).first()
    if not trainee_user:
        return
    trainer_display = trainer_user.get_full_name() or trainer_user.username
    notification = questions.objects.create(
        name=trainer_display,
        email=trainer_user.email or '',
        quest=f'Training plan {action_label}: {plan.get_split_type_display()}',
    )
    split_info = ', '.join(plan.split_days) if plan.split_days else 'Custom split'
    response_model.objects.create(
        name=trainer_user,
        quest=notification,
        text=(
            f'Your trainer {trainer_display} has {action_label} your training plan.\n\n'
            f'Split: {plan.get_split_type_display()}\n'
            f'Days: {split_info}\n'
            f'Week: {plan.start_date} – {plan.end_date}\n\n'
            f'Check your schedule to see the details.'
        ),
        is_read=False,
    )


@login_required
def training_plan_view(request, trainee_id):
    trainee = get_object_or_404(names, id=trainee_id, role=names.ROLE_TRAINEE)
    is_trainer = hasattr(request.user, 'profile') and request.user.profile.is_trainer
    is_assigned_trainer = is_trainer and trainee.trainer == request.user
    is_trainee_owner = False
    if trainee.role == names.ROLE_TRAINEE:
        if request.user.email and trainee.email and request.user.email.lower() == trainee.email.lower():
            is_trainee_owner = True
        elif trainee.trainer == request.user:
            pass
        elif request.user.is_authenticated:
            user_record = names.objects.filter(
                Q(email__iexact=request.user.email) |
                Q(name__iexact=request.user.username) |
                Q(name__iexact=request.user.get_full_name()),
                role=names.ROLE_TRAINEE
            ).first()
            if user_record and user_record.id == trainee.id:
                is_trainee_owner = True

    if not (request.user.is_superuser or is_assigned_trainer or is_trainee_owner):
        messages.error(request, 'You do not have access to this training plan.')
        return redirect('home_url')

    trainer_names = None
    if is_assigned_trainer:
        trainer_names = names.objects.filter(email=request.user.email, role=names.ROLE_TRAINER).first()

    today = date.today()
    current_week_start = today - timedelta(days=today.weekday())

    week_start_str = request.GET.get('week_start', '')
    if week_start_str:
        try:
            week_start = date.fromisoformat(week_start_str)
        except (ValueError, TypeError):
            week_start = current_week_start
    else:
        week_start = current_week_start

    week_end = week_start + timedelta(days=6)

    plan = TrainingPlan.objects.filter(
        trainee=trainee, start_date__lte=week_end, end_date__gte=week_start, is_active=True
    ).first()

    if request.method == 'POST' and is_assigned_trainer:
        action = request.POST.get('action')

        if action == 'create_plan':
            split_type = request.POST.get('split_type')
            if split_type:
                plan = TrainingPlan.objects.create(
                    trainee=trainee,
                    trainer=trainer_names,
                    split_type=split_type,
                    start_date=week_start,
                    end_date=week_end,
                )
                split_days = plan.split_days
                for i, label in enumerate(split_days):
                    TrainingPlanDay.objects.create(
                        plan=plan, day_index=i, day_label=label, is_rest_day=False, exercises=[]
                    )
                _notify_trainee_plan_update(request.user, trainee, plan, 'created a new')
                messages.success(request, f'Training plan created with split: {plan.get_split_type_display()}')
            return redirect(f'{request.path}?week_start={week_start}')

        elif action == 'update_exercises':
            day_id = request.POST.get('day_id')
            day = get_object_or_404(TrainingPlanDay, id=day_id, plan__trainee=trainee)
            exercises = []
            exercise_names = request.POST.getlist(f'exercise_name_{day_id}[]')
            exercise_sets = request.POST.getlist(f'exercise_sets_{day_id}[]')
            exercise_reps = request.POST.getlist(f'exercise_reps_{day_id}[]')
            exercise_weight = request.POST.getlist(f'exercise_weight_{day_id}[]')
            exercise_notes = request.POST.getlist(f'exercise_notes_{day_id}[]')
            for j in range(len(exercise_names)):
                if exercise_names[j].strip():
                    exercises.append({
                        'name': exercise_names[j].strip(),
                        'sets': exercise_sets[j].strip() if j < len(exercise_sets) else '',
                        'reps': exercise_reps[j].strip() if j < len(exercise_reps) else '',
                        'weight': exercise_weight[j].strip() if j < len(exercise_weight) else '',
                        'notes': exercise_notes[j].strip() if j < len(exercise_notes) else '',
                    })
            day.exercises = exercises
            day.save()
            _notify_trainee_plan_update(request.user, trainee, day.plan, 'updated exercises for')
            messages.success(request, f'Exercises updated for {day.day_label or f"Day {day.day_index + 1}"}')
            return redirect(f'{request.path}?week_start={week_start}')

        elif action == 'toggle_rest':
            day_id = request.POST.get('day_id')
            day = get_object_or_404(TrainingPlanDay, id=day_id, plan__trainee=trainee)
            day.is_rest_day = not day.is_rest_day
            day.exercises = []
            day.save()
            return redirect(f'{request.path}?week_start={week_start}')

        elif action == 'update_notes':
            plan_id = request.POST.get('plan_id')
            plan_obj = get_object_or_404(TrainingPlan, id=plan_id, trainee=trainee)
            plan_obj.notes = request.POST.get('notes', '')
            plan_obj.save()
            messages.success(request, 'Plan notes updated.')
            return redirect(f'{request.path}?week_start={week_start}')

        elif action == 'change_split':
            plan_id = request.POST.get('plan_id')
            new_split = request.POST.get('split_type')
            plan_obj = get_object_or_404(TrainingPlan, id=plan_id, trainee=trainee)
            plan_obj.split_type = new_split
            plan_obj.save()
            plan_obj.days.all().delete()
            split_days = plan_obj.split_days
            for i, label in enumerate(split_days):
                TrainingPlanDay.objects.create(
                    plan=plan_obj, day_index=i, day_label=label, is_rest_day=False, exercises=[]
                )
            _notify_trainee_plan_update(request.user, trainee, plan_obj, 'changed your split to')
            messages.success(request, f'Split changed to: {plan_obj.get_split_type_display()}')
            return redirect(f'{request.path}?week_start={week_start}')

    week_dates = [week_start + timedelta(days=i) for i in range(7)]

    existing_plans = TrainingPlan.objects.filter(trainee=trainee, is_active=True).order_by('-start_date')

    # Get split progression info
    progression, _ = SplitProgression.objects.get_or_create(trainee=trainee)
    next_body_part = None
    current_day_number = None
    total_days = 0
    split_type_display = None

    # Try to get from active plan first
    if plan and plan.split_days:
        day_index = progression.current_day_index % len(plan.split_days)
        next_body_part = plan.split_days[day_index]
        current_day_number = day_index + 1
        total_days = len(plan.split_days)
        split_type_display = plan.get_split_type_display()
    else:
        # Fall back to most recent plan
        latest_plan = existing_plans.first()
        if latest_plan and latest_plan.split_days:
            day_index = progression.current_day_index % len(latest_plan.split_days)
            next_body_part = latest_plan.split_days[day_index]
            current_day_number = day_index + 1
            total_days = len(latest_plan.split_days)
            split_type_display = latest_plan.get_split_type_display()

    context = {
        'trainee': trainee,
        'is_assigned_trainer': is_assigned_trainer,
        'is_trainee_owner': is_trainee_owner,
        'plan': plan,
        'plan_days': plan.days.all() if plan else [],
        'week_start': week_start,
        'week_end': week_end,
        'week_dates': week_dates,
        'prev_week': week_start - timedelta(days=7),
        'next_week': week_start + timedelta(days=7),
        'today': today,
        'existing_plans': existing_plans,
        'split_choices': TrainingPlan.SPLIT_CHOICES,
        'next_body_part': next_body_part,
        'current_day_number': current_day_number,
        'total_days': total_days,
        'total_workouts': progression.total_workouts_completed,
        'split_type_display': split_type_display,
    }
    return render(request, 'training_plan.html', context)


@_require_trainer
def trainer_my_schedule(request):
    trainer_names = names.objects.filter(email=request.user.email, role=names.ROLE_TRAINER).first()
    if not trainer_names:
        messages.error(request, 'Trainer profile not found.')
        return redirect('home_url')

    schedules = TrainerSchedule.objects.filter(trainer=trainer_names).order_by('day_of_week', 'shift')

    if request.method == 'POST':
        schedule_id = request.POST.get('schedule_id')
        comment_text = request.POST.get('comment', '').strip()
        if schedule_id:
            schedule = get_object_or_404(TrainerSchedule, id=schedule_id, trainer=trainer_names)
            schedule.trainer_comment = comment_text
            schedule.comment_updated_at = timezone.now()
            schedule.save()

            day_label = schedule.get_day_of_week_display()
            shift_label = schedule.get_shift_display()
            notification = questions.objects.create(
                name=trainer_names.name or request.user.username,
                email=request.user.email or '',
                quest=f'Schedule comment from {trainer_names.name}: {day_label} {shift_label}\n\nComment: {comment_text}',
            )
            response_model.objects.create(
                name=request.user,
                quest=notification,
                text=(
                    f'{trainer_names.name} commented on their schedule:\n\n'
                    f'Day: {day_label}\n'
                    f'Shift: {shift_label} ({schedule.shift_start()} - {schedule.shift_end()})\n\n'
                    f'Comment: {comment_text}'
                ),
                is_read=False,
            )

            messages.success(request, 'Your comment has been sent to the admin.')
            return redirect('trainer_my_schedule_url')

    # Generate 4-week calendar
    today = timezone.now().date()
    # Start from today
    calendar_weeks = []
    for week_offset in range(4):
        week_start = today + timedelta(weeks=week_offset)
        week_days = []
        for day_offset in range(7):
            current_date = week_start + timedelta(days=day_offset)
            # Convert Python weekday (Mon=0) to our schedule weekday (Sun=0)
            py_weekday = current_date.weekday()
            schedule_weekday = (py_weekday + 1) % 7

            # Find matching schedule entries
            day_schedules = [s for s in schedules if s.day_of_week == schedule_weekday]

            week_days.append({
                'date': current_date,
                'day_name': ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'][schedule_weekday],
                'schedules': day_schedules,
                'is_today': current_date == today,
            })
        calendar_weeks.append({
            'week_number': week_offset + 1,
            'days': week_days,
        })

    return render(request, 'trainer_my_schedule.html', {
        'schedules': schedules,
        'trainer': trainer_names,
        'calendar_weeks': calendar_weeks,
        'today': today,
    })


def debug_email(request):
    from pathlib import Path
    from django.conf import settings
    from django.core.mail import send_mail
    
    test_result = None
    if request.GET.get('test'):
        try:
            send_mail(
                'Test Email',
                'This is a test email from Future Gym.',
                settings.DEFAULT_FROM_EMAIL,
                [settings.EMAIL_HOST_USER],
                fail_silently=False,
            )
            test_result = 'SUCCESS: Email sent! Check Render logs for output.'
        except Exception as e:
            test_result = f'ERROR: {type(e).__name__}: {str(e)}'
    
    error_file = Path(__file__).parent.parent / 'email_errors.log'
    if error_file.exists():
        error_content = error_file.read_text()
    else:
        error_content = 'No email errors logged yet.'
    
    debug_info = f"""EMAIL BACKEND: {settings.EMAIL_BACKEND}
EMAIL HOST USER: {getattr(settings, 'EMAIL_HOST_USER', 'Not set')}
DEFAULT FROM EMAIL: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'Not set')}

TEST RESULT:
{test_result or 'Not tested yet. Click the button below to test.'}

ERRORS:
{error_content}
"""
    html = f'<pre>{debug_info}</pre>'
    html += '<form method="get"><button type="submit" name="test" value="1" style="padding: 10px 20px; font-size: 16px;">Send Test Email (prints to logs)</button></form>'
    return HttpResponse(html)


import uuid
import hashlib

MEMBERSHIP_FEE = 5000
SUBSCRIPTION_MONTHS = 3

@login_required
def membership_payment_page(request):
    user = request.user
    latest_payment = MembershipPayment.objects.filter(user=user).order_by('-entry_date').first()
    all_payments = MembershipPayment.objects.filter(user=user).order_by('-entry_date')

    is_active = False
    subscription_end = None
    if latest_payment and latest_payment.subscription_end:
        from datetime import date
        subscription_end = latest_payment.subscription_end
        is_active = subscription_end >= date.today()

    context = {
        'latest_payment': latest_payment,
        'all_payments': all_payments,
        'is_active': is_active,
        'subscription_end': subscription_end,
        'membership_fee': MEMBERSHIP_FEE,
        'subscription_months': SUBSCRIPTION_MONTHS,
    }
    return render(request, 'membership_payment.html', context)


@login_required
def chapa_checkout(request):
    if request.method == 'POST':
        tx_ref = f"TX-{uuid.uuid4().hex[:12].upper()}"
        user = request.user

        from datetime import date
        today = date.today()
        sub_start = today
        sub_end = today + timedelta(days=SUBSCRIPTION_MONTHS * 30)

        receipt_num = f"FG-{uuid.uuid4().hex[:8].upper()}"

        payment = MembershipPayment.objects.create(
            user=user,
            amount=MEMBERSHIP_FEE,
            payment_date=today,
            payment_method='CHAPA',
            receipt_number=receipt_num,
            is_verified=True,
            subscription_start=sub_start,
            subscription_end=sub_end,
            chapa_tx_ref=tx_ref,
        )

        receipt_notice = questions.objects.create(
            name=user.username,
            email=user.email,
            quest=f"Payment Logged: {MEMBERSHIP_FEE} via CHAPA on {today}."
        )
        response_model.objects.create(
            name=user,
            quest=receipt_notice,
            text=f"Official Confirmation: Your payment of {MEMBERSHIP_FEE} ETB has been verified via Chapa. Your membership is active until {sub_end}."
        )

        return redirect('payment_receipt_url', payment_id=payment.id)

    context = {
        'membership_fee': MEMBERSHIP_FEE,
        'subscription_months': SUBSCRIPTION_MONTHS,
    }
    return render(request, 'chapa_checkout.html', context)


@login_required
def payment_receipt(request, payment_id):
    payment = get_object_or_404(MembershipPayment, id=payment_id, user=request.user)
    context = {
        'payment': payment,
    }
    return render(request, 'payment_receipt.html', context)


@user_passes_test(lambda u: u.is_superuser, login_url='login_url')
def income_report(request):
    from datetime import date, timedelta
    from decimal import Decimal
    import calendar

    TAX_RATE = Decimal('0.30')

    today = date.today()
    current_month = today.month
    current_year = today.year

    period = request.GET.get('period', 'all')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if period == 'month':
        period_start = date(current_year, current_month, 1)
        period_end = date(current_year, current_month, calendar.monthrange(current_year, current_month)[1])
        period_label = today.strftime('%B %Y')
    elif period == 'year':
        period_start = date(current_year, 1, 1)
        period_end = date(current_year, 12, 31)
        period_label = str(current_year)
    elif period == 'custom' and start_date and end_date:
        period_start = datetime.strptime(start_date, '%Y-%m-%d').date()
        period_end = datetime.strptime(end_date, '%Y-%m-%d').date()
        period_label = f"{period_start.strftime('%d %b %Y')} - {period_end.strftime('%d %b %Y')}"
    else:
        period_start = None
        period_end = None
        period_label = 'All Time'

    all_payments = MembershipPayment.objects.filter(
        is_verified=True,
        user__profile__role='trainee'
    )

    if period_start and period_end:
        all_payments = all_payments.filter(
            payment_date__gte=period_start,
            payment_date__lte=period_end
        )

    gross_income = all_payments.aggregate(
        total=Coalesce(Sum('amount'), Decimal('0.00'))
    )['total']

    monthly_income = all_payments.filter(
        payment_date__year=current_year,
        payment_date__month=current_month,
    ).aggregate(
        total=Coalesce(Sum('amount'), Decimal('0.00'))
    )['total']

    income_by_method = all_payments.values('payment_method').annotate(
        total=Coalesce(Sum('amount'), Decimal('0.00')),
        count=Count('id')
    ).order_by('-total')

    monthly_breakdown = all_payments.annotate(
        month=TruncMonth('payment_date')
    ).values('month').annotate(
        total=Coalesce(Sum('amount'), Decimal('0.00')),
        count=Count('id')
    ).order_by('month')[:12]

    total_payments_count = all_payments.count()
    unique_payers = all_payments.values('user').distinct().count()

    employee_payments = TrainerPayment.objects.select_related('trainer').all().order_by('trainer__name')
    total_workers = employee_payments.count()
    monthly_expenses = employee_payments.aggregate(
        total=Coalesce(Sum('salary'), Decimal('0.00'))
    )['total']

    if period_start and period_end:
        months_in_range = (period_end.year - period_start.year) * 12 + (period_end.month - period_start.month) + 1
        total_expenses = monthly_expenses * months_in_range
    else:
        total_expenses = monthly_expenses

    net_before_tax = gross_income - total_expenses
    tax_amount = max(net_before_tax * TAX_RATE, Decimal('0.00'))
    net_income = net_before_tax - tax_amount

    net_monthly_before_tax = monthly_income - monthly_expenses
    monthly_tax = max(net_monthly_before_tax * TAX_RATE, Decimal('0.00'))
    net_monthly = net_monthly_before_tax - monthly_tax

    recent_payments = all_payments.select_related('user').order_by('-payment_date')[:20]

    worker_details = []
    for tp in employee_payments:
        worker_details.append({
            'name': tp.trainer.name,
            'role': tp.trainer.role,
            'salary': tp.salary,
            'frequency': tp.get_payment_frequency_display(),
            'next_due': tp.next_payment_due,
            'days_until': tp.days_until_payment,
        })

    context = {
        'gross_income': gross_income,
        'monthly_income': monthly_income,
        'net_income': net_income,
        'net_monthly': net_monthly,
        'total_expenses': total_expenses,
        'monthly_expenses': monthly_expenses,
        'tax_amount': tax_amount,
        'monthly_tax': monthly_tax,
        'tax_rate': TAX_RATE * 100,
        'net_before_tax': net_before_tax,
        'total_payments_count': total_payments_count,
        'unique_payers': unique_payers,
        'total_workers': total_workers,
        'income_by_method': income_by_method,
        'monthly_breakdown': monthly_breakdown,
        'recent_payments': recent_payments,
        'worker_details': worker_details,
        'period_label': period_label,
        'current_period': period,
        'start_date': start_date or '',
        'end_date': end_date or '',
    }
    return render(request, 'income_report.html', context)