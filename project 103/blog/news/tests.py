from django.test import TestCase
from django.contrib.auth.models import User

from .forms import TraineeAccountForm, UserRegisterForm
from .models import names, TrainingSession, UserProfile


class UserRegistrationValidationTests(TestCase):
    def test_duplicate_email_is_rejected(self):
        User.objects.create_user(username='existing', email='member@gmail.com', password='password')

        form = UserRegisterForm(data={
            'username': 'newmember',
            'email': 'MEMBER@GMAIL.COM',
            'phone_number': '0912345678',
            'password1': 'StrongPassword123!',
            'password2': 'StrongPassword123!',
        })

        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)


class AccountUpdateFormTests(TestCase):
    def test_full_name_is_not_part_of_account_update_form(self):
        form = TraineeAccountForm(data={
            'email': 'member@gmail.com',
            'phone_number': '0912345678',
        })

        self.assertNotIn('full_name', form.fields)
        self.assertTrue(form.is_valid())


class TrainingSessionApprovalTests(TestCase):
    def test_new_session_requires_approval(self):
        trainer = names.objects.create(name='Trainer One', role=names.ROLE_TRAINER)
        session = TrainingSession.objects.create(
            title='Strength Class',
            session_date='2030-01-01T10:00:00Z',
            max_trainees=10,
            trainer=trainer,
        )

        self.assertEqual(session.approval_status, TrainingSession.STATUS_PENDING)

    def test_duplicate_phone_is_rejected(self):
        names.objects.create(
            name='Existing Member',
            email='existing@example.com',
            phone_number='+251912345678',
        )

        form = UserRegisterForm(data={
            'username': 'newmember',
            'email': 'newmember@example.com',
            'phone_number': '0912345678',
            'password1': 'StrongPassword123!',
            'password2': 'StrongPassword123!',
        })

        self.assertFalse(form.is_valid())
        self.assertIn('phone_number', form.errors)

    def test_gmail_and_ethiopian_phone_are_normalized(self):
        form = UserRegisterForm(data={
            'username': 'newmember',
            'email': 'Member@GMAIL.COM',
            'phone_number': '0912345678',
            'password1': 'StrongPassword123!',
            'password2': 'StrongPassword123!',
        })

        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['email'], 'member@gmail.com')
        self.assertEqual(form.cleaned_data['phone_number'], '+251912345678')

    def test_non_gmail_address_is_rejected(self):
        form = UserRegisterForm(data={
            'username': 'newmember',
            'email': 'newmember@example.com',
            'phone_number': '0912345678',
            'password1': 'StrongPassword123!',
            'password2': 'StrongPassword123!',
        })

        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)


class TrainingPlanErrorTests(TestCase):
    def test_trainee_without_trainer_receives_no_trainer_500_page(self):
        user = User.objects.create_user(
            username='trainee',
            email='trainee@example.com',
            password='password',
        )
        UserProfile.objects.create(user=user, role=UserProfile.ROLE_TRAINEE)
        trainee = names.objects.create(
            name='Trainee',
            email=user.email,
            role=names.ROLE_TRAINEE,
        )
        self.client.force_login(user)

        response = self.client.get(f'/training-plan/{trainee.id}/')

        self.assertEqual(response.status_code, 500)
        self.assertContains(response, 'No trainer', status_code=500)

    def test_trainee_without_trainer_cannot_open_detail_page(self):
        user = User.objects.create_user(
            username='trainee',
            email='trainee@example.com',
            password='password',
        )
        UserProfile.objects.create(user=user, role=UserProfile.ROLE_TRAINEE)
        names.objects.create(
            name='Trainee',
            email=user.email,
            role=names.ROLE_TRAINEE,
        )
        names.objects.create(
            name='Other Trainee',
            email='other@example.com',
            role=names.ROLE_TRAINEE,
        )
        self.client.force_login(user)

        response = self.client.get('/detail/Other Trainee')

        self.assertEqual(response.status_code, 500)
        self.assertContains(response, 'No trainer', status_code=500)

    def test_trainee_without_trainer_can_open_trainer_detail_page(self):
        user = User.objects.create_user(
            username='trainee',
            email='trainee@example.com',
            password='password',
        )
        UserProfile.objects.create(user=user, role=UserProfile.ROLE_TRAINEE)
        names.objects.create(
            name='Trainee',
            email=user.email,
            role=names.ROLE_TRAINEE,
        )
        names.objects.create(
            name='John',
            email='john@example.com',
            role=names.ROLE_TRAINER,
        )
        self.client.force_login(user)

        response = self.client.get('/detail/John')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'John')

    def test_trainer_account_can_open_detail_when_legacy_role_is_stale(self):
        user = User.objects.create_user(
            username='trainee',
            email='trainee@example.com',
            password='password',
        )
        UserProfile.objects.create(user=user, role=UserProfile.ROLE_TRAINEE)
        names.objects.create(
            name='Trainee',
            email=user.email,
            role=names.ROLE_TRAINEE,
        )
        trainer_user = User.objects.create_user(
            username='john',
            email='john@example.com',
            password='password',
        )
        UserProfile.objects.create(user=trainer_user, role=UserProfile.ROLE_TRAINER)
        names.objects.create(
            name='John',
            email=trainer_user.email,
            role=names.ROLE_TRAINEE,
        )
        self.client.force_login(user)

        response = self.client.get('/detail/John')

        self.assertEqual(response.status_code, 200)

    def test_home_trainer_button_is_disabled_without_trainer(self):
        user = User.objects.create_user(
            username='trainee',
            email='trainee@example.com',
            password='password',
        )
        UserProfile.objects.create(user=user, role=UserProfile.ROLE_TRAINEE)
        names.objects.create(
            name='Trainee',
            email=user.email,
            role=names.ROLE_TRAINEE,
        )
        self.client.force_login(user)

        response = self.client.get('/home/')

        self.assertContains(response, 'aria-disabled="true"')
        self.assertNotContains(response, 'href="/detail/John"')
