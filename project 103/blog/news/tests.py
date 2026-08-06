from django.test import TestCase
from django.contrib.auth.models import User

from .forms import UserRegisterForm
from .models import names


class UserRegistrationValidationTests(TestCase):
    def test_duplicate_email_is_rejected(self):
        User.objects.create_user(username='existing', email='member@example.com', password='password')

        form = UserRegisterForm(data={
            'username': 'newmember',
            'email': 'MEMBER@example.com',
            'phone_number': '555-0100',
            'password1': 'StrongPassword123!',
            'password2': 'StrongPassword123!',
        })

        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_duplicate_phone_is_rejected(self):
        names.objects.create(
            name='Existing Member',
            email='existing@example.com',
            phone_number='555-0100',
        )

        form = UserRegisterForm(data={
            'username': 'newmember',
            'email': 'newmember@example.com',
            'phone_number': '555-0100',
            'password1': 'StrongPassword123!',
            'password2': 'StrongPassword123!',
        })

        self.assertFalse(form.is_valid())
        self.assertIn('phone_number', form.errors)
