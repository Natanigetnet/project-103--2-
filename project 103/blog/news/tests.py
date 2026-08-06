from django.test import TestCase
from django.contrib.auth.models import User

from .forms import UserRegisterForm
from .models import names


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
