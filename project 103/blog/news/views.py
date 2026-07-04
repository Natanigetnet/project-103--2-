from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import HttpResponse
from django.utils.html import format_html   
from .models import names,comments,Category,questions,response_model,TrainingSession,BodyMetric,TrainingSpace,MemberID,AttendanceLog,TrainerRating,TrainerChangeRequest,TrainingPlan,TrainingPlanDay
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.backends import ModelBackend
from django.contrib import messages
from functools import wraps
from django.db.models import Avg, Count, Q

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
from django.core.mail import send_mail
import uuid
from django.core.validators import RegexValidator
import secrets
import string

import json

@user_passes_test(lambda u: u.is_superuser, login_url='login_url')
def admin_dash(request):
    return render(request, 'admin.html')
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
                try:
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
                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        [email],
                        fail_silently=False,
                    )
                    email_sent = True
                except Exception as e:
                    messages.warning(
                        request,
                        f"Account created, but we could not send a confirmation email: {str(e)}",
                    )

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
        'action_label': 'New Desk',
        'create_url': 'register_url',
        'delete_redirect': 'manage_staff_url',
    })


def notify_trainer_of_assignment(trainer_user, member, assigned_by=None):
    """Email and in-app message when a trainee is assigned to a trainer."""
    trainee_name = member.name or 'Trainee'
    category_label = member.category.name if member.category else 'Not set'
    phone = member.phone_number or '—'
    trainee_email = member.email or '—'

    email_body = f"""Hello {trainer_user.get_full_name() or trainer_user.username},

A new trainee has been assigned to you at Future Gym.

Trainee: {trainee_name}
Email: {trainee_email}
Phone: {phone}
Category: {category_label}

Log in and open Tracker to view your assigned members.

Best regards,
Future Gym Management
"""
    if trainer_user.email:
        try:
            send_mail(
                'Future Gym – New trainee assigned to you',
                email_body,
                settings.DEFAULT_FROM_EMAIL,
                [trainer_user.email],
                fail_silently=False,
            )
        except Exception:
            pass

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
    if request.user.is_authenticated and not request.user.is_superuser:
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

    context = {
        'unread_count': unread_count,
        'is_trainee': is_trainee,
        'is_registrar': is_registrar,
        'spaces': spaces_for_modal,
        'upcoming_sessions': upcoming_sessions,
        'assigned_trainer_name': assigned_trainer_name,
        'my_detail_name': my_detail_name,
        'my_trainee_id': my_trainee_id,
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
        form = TraineeAccountForm(request.POST, request.FILES)
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
        form = TraineeAccountForm(initial=initial)

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
        form = TraineeAccountForm(request.POST, request.FILES)
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
        form = TraineeAccountForm(initial=initial)

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

_FAQ = [
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
        'Our gym is open Monday–Friday 6:00 AM – 10:00 PM, Saturday 8:00 AM – 8:00 PM, '
        'and Sunday 9:00 AM – 6:00 PM. Category-specific training spaces may have separate schedules.'
    )),
    (r'(?i)\b(membership|price|cost|fee|subscription|sign.?up|join)\b', (
        'Future Gym offers monthly and annual membership plans. Please contact our front desk '
        'or visit the gym for current pricing and any promotional offers.'
    )),
    (r'(?i)\b(park|parking|car|location|address|find|directions)\b', (
        'Future Gym is located at 123 Tech Avenue, Silicon Valley, CA. Free parking is '
        'available for members in the adjacent lot.'
    )),
    (r'(?i)\b(phone|contact|call|reach|email|support|help)\b', (
        'You can reach us at +1 (555) 000-TECH or email hello@futuregym.com. '
        'You can also submit questions here and a trainer will respond.'
    )),
    (r'(?i)^\s*(hi|hello|hey|good\s*(morning|afternoon|evening)|sup|yo|hey.?\s*there)\s*[.!?]*\s*$', (
        'Hello! Welcome to Future Gym support. How can I help you today?'
    )),
]


def _local_responder(question_text):
    """Answer common gym questions without any external API."""
    for pattern, answer in _FAQ:
        if re.search(pattern, question_text):
            return answer, True
    return None, False


def ask_ai(question_text):
    """Try Gemini Flash first, fall back to local keyword matching."""
    # Try Gemini if API key is configured
    api_key = settings.GEMINI_API_KEY
    if api_key:
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            prompt = (
                "You are a helpful assistant for Future Gym. Answer the following question "
                "about gym memberships, training programs, class schedules, or general fitness. "
                "If the question is not related to the gym, fitness, or health, "
                "respond with exactly: UNABLE_TO_ANSWER\n\n"
                f"Question: {question_text}"
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

    # Fall back to local keyword responder
    return _local_responder(question_text)


def chat_page(request):
    return render(request, 'chat.html')

@require_http_methods(["POST"])
def chat_api(request):
    try:
        data = json.loads(request.body)
        message = data.get('message', '')
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({'error': 'Invalid request'}, status=400)

    if not message.strip():
        return JsonResponse({'error': 'Message is required'}, status=400)

    answer, answered = ask_ai(message)
    if answered:
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

        # Send email with credentials
        try:
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

            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            messages.success(request, f"Account created successfully! Credentials sent to {email}")
        except Exception as e:
            messages.warning(request, f"Account created but email could not be sent: {str(e)}")

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

    if request.method == 'POST':
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
    return render(request, 'trainee_bmi.html', {'metrics': metrics, 'progress': progress})


@login_required
def trainer_bmi_tracker(request):
    user_profile = UserProfile.objects.filter(user=request.user).first()
    if not user_profile or not user_profile.is_trainer:
        messages.error(request, 'Access restricted to trainers.')
        return redirect('home_url')

    assigned_trainees = names.objects.filter(trainer=request.user, role=names.ROLE_TRAINEE).order_by('-date')

    trainees_data = []
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
        trainees_data.append({
            'trainee': trainee,
            'user': user_obj,
            'latest': latest,
            'weight_change': weight_change,
            'metrics': all_metrics,
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

    return render(request, 'session_list.html', {
        'trainer': trainer_user,
        'sessions': session_rows,
        'trainee': trainee_profile,
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
    from io import BytesIO
    from django.core.files.base import ContentFile

    qr = qrcode.QRCode(box_size=10, border=2)
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
    from io import BytesIO
    import base64

    qr = qrcode.QRCode(box_size=10, border=2)
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
def generate_all_missing_ids(request):
    if not request.user.is_superuser:
        messages.error(request, "Admin only.")
        return redirect('home_url')
    count = 0
    for person in names.objects.all():
        mid, created = MemberID.objects.get_or_create(member=person)
        if created or not mid.qr_code or not mid.unique_id:
            mid.unique_id = str(uuid.uuid4())
            generate_qr_image(mid)
            count += 1
    messages.success(request, f"Generated {count} ID card(s). All members now have IDs.")
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
        return JsonResponse({'ok': False, 'error': 'Unknown ID card'}, status=404)

    # Find today's active check-in for this member
    today = timezone.localtime(timezone.now()).date()
    active = AttendanceLog.objects.filter(
        member=mid.member,
        check_in__date=today,
        check_out__isnull=True
    ).first()

    if active is not None:
        active.check_out = timezone.now()
        active.checked_out_by = request.user if request.user.is_authenticated else None
        active.save(update_fields=['check_out', 'checked_out_by'])
        return JsonResponse({
            'ok': True,
            'action': 'checkout',
            'member_name': mid.member.name,
            'role': mid.member.role,
            'check_in': timezone.localtime(active.check_in).strftime('%H:%M'),
            'check_out': timezone.localtime(active.check_out).strftime('%H:%M'),
        })

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
        return JsonResponse({'ok': False, 'error': 'Unknown ID card'}, status=404)

    today = timezone.localtime(timezone.now()).date()
    active = AttendanceLog.objects.filter(
        member=mid.member,
        check_in__date=today,
        check_out__isnull=True
    ).first()
    if active:
        active.check_out = timezone.now()
        active.checked_out_by = request.user if request.user.is_authenticated else None
        active.save(update_fields=['check_out', 'checked_out_by'])
        return JsonResponse({
            'ok': True,
            'action': 'checkout',
            'member_name': mid.member.name,
            'role': mid.member.role,
            'check_in': timezone.localtime(active.check_in).strftime('%H:%M'),
            'check_out': timezone.localtime(active.check_out).strftime('%H:%M'),
        })

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
        return JsonResponse({'ok': False, 'error': 'Unknown ID card'}, status=404)

    today = timezone.localtime(timezone.now()).date()
    attendance = AttendanceLog.objects.filter(
        member=mid.member,
        check_in__date=today,
        check_out__isnull=True
    ).first()

    if not attendance:
        return JsonResponse({'ok': False, 'error': 'No active check-in found for today'}, status=404)

    attendance.check_out = timezone.now()
    attendance.checked_out_by = request.user if request.user.is_authenticated else None
    attendance.save(update_fields=['check_out', 'checked_out_by'])

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
        return JsonResponse({'ok': False, 'error': 'Unknown ID card'}, status=404)

    today = timezone.localtime(timezone.now()).date()
    active = AttendanceLog.objects.filter(
        member=mid.member,
        check_in__date=today,
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
    today_logs = AttendanceLog.objects.filter(
        check_in__gte=today_start,
        check_out__isnull=True,
        member__trainer=request.user
    ).select_related('member', 'member__category').order_by('-check_in')
    members_in = {}
    for log in today_logs:
        mid = log.member_id
        if mid not in members_in:
            members_in[mid] = log
    currently_in = list(members_in.values())
    total = len(currently_in)
    return render(request, 'trainer_currently_in.html', {
        'currently_in': currently_in,
        'total': total,
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
    today_logs = AttendanceLog.objects.filter(check_in__gte=today_start).select_related('member', 'member__category')

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

        try:
            subject = "Welcome to Future Gym - Your Account Details"
            message = f"""Dear {name},

Welcome to Future Gym! Your account has been created.

Username: {username}
Password: {password}
Email: {email}

Please log in and change your password immediately.

Best regards,
Future Gym Management"""
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email], fail_silently=True)
        except Exception:
            pass

        messages.success(request, f'Trainee "{name}" registered successfully! Username: {username}, Password: {password}')
        return redirect('registrar_dashboard_url')

    return render(request, 'registrar_register.html', {'categories': all_categories})


@_require_registrar
def registrar_scan_qr(request):
    attendance = AttendanceLog.objects.select_related('member', 'checked_in_by').order_by('-check_in')[:50]
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
    }
    return render(request, 'training_plan.html', context)