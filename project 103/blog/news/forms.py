from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
import re
from .models import Category, UserProfile, names, FeedPost


def normalize_gmail(email):
    email = (email or '').strip().lower()
    if not email:
        return email
    try:
        validate_email(email)
    except ValidationError:
        raise forms.ValidationError('Enter a valid Gmail address, for example name@gmail.com.')
    if not email.endswith('@gmail.com'):
        raise forms.ValidationError('Use a Gmail address ending in @gmail.com.')
    return email


def normalize_ethiopian_phone(phone_number):
    phone_number = re.sub(r'[\s()\-]', '', (phone_number or '').strip())
    if not phone_number:
        return phone_number

    if phone_number.startswith('+251'):
        local_number = phone_number[4:]
    elif phone_number.startswith('251'):
        local_number = phone_number[3:]
    elif phone_number.startswith('0'):
        local_number = phone_number[1:]
    else:
        local_number = phone_number

    if not re.fullmatch(r'[79]\d{8}', local_number):
        raise forms.ValidationError(
            'Enter an Ethiopian mobile number like +251912345678 or 0912345678.'
        )
    return f'+251{local_number}'


class TraineeAccountForm(forms.Form):
    full_name = forms.CharField(max_length=40, label='Full name')
    email = forms.EmailField(label='Email address')
    phone_number = forms.CharField(max_length=20, label='Phone number', required=False)
    gender = forms.ChoiceField(
        choices=UserProfile.GENDER_CHOICES,
        required=False,
        label='Gender',
    )
    image = forms.ImageField(required=False, label='Profile picture')

    def __init__(self, *args, exclude_user=None, **kwargs):
        self.exclude_user = exclude_user
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.setdefault('class', 'form-select')
            else:
                field.widget.attrs.setdefault('class', 'form-control')


class TraineeMedicalForm(forms.Form):
    medical_info = forms.CharField(
        label='Medical information',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 8,
            'placeholder': 'Allergies, injuries, medications, conditions, emergency contacts, or notes for your trainer…',
        }),
    )

class UserRegisterForm(UserCreationForm):
    full_name = forms.CharField(max_length=40, label='Full name', required=False)
    phone_number = forms.CharField(max_length=20, label='Phone number', required=False)
    email = forms.EmailField(required=True)
    ROLE_CHOICES = [
        ('trainee', 'Trainee'),
        ('trainer', 'Trainer'),
    ]
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
    ]
    role = forms.ChoiceField(choices=ROLE_CHOICES, required=False)
    gender = forms.ChoiceField(choices=GENDER_CHOICES, required=False)
    category = forms.ModelChoiceField(queryset=Category.objects.all(), required=False)

    class Meta:
        model = User
        fields = ['username', 'email']

    def __init__(self, *args, require_profile_fields=False, **kwargs):
        super().__init__(*args, **kwargs)
        if require_profile_fields:
            self.fields['full_name'].required = True
            self.fields['phone_number'].required = True
            field_order = [
                'full_name', 'phone_number', 'gender',
                'username', 'email', 'password1', 'password2',
            ]
        else:
            field_order = [
                'full_name', 'phone_number', 'username', 'email',
                'password1', 'password2', 'role', 'gender', 'category',
            ]
        self.order_fields([f for f in field_order if f in self.fields])
        self.fields['email'].widget.attrs.setdefault('placeholder', 'name@gmail.com')
        self.fields['phone_number'].widget.attrs.setdefault('placeholder', '+251912345678')
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.TextInput) or isinstance(field.widget, forms.EmailInput):
                field.widget.attrs.setdefault('class', 'form-control')
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.setdefault('class', 'form-select')
            elif isinstance(field.widget, forms.PasswordInput):
                field.widget.attrs.setdefault('class', 'form-control')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data.get('email', '')
        if commit:
            user.save()
        return user

    def clean_email(self):
        email = normalize_gmail(self.cleaned_data['email'])
        if User.objects.filter(email__iexact=email).exists() or names.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email address already exists.')
        return email

    def clean_phone_number(self):
        phone_number = normalize_ethiopian_phone(self.cleaned_data.get('phone_number', ''))
        if phone_number and names.objects.filter(phone_number__iexact=phone_number).exists():
            raise forms.ValidationError('An account with this phone number already exists.')
        return phone_number


class FeedPostForm(forms.ModelForm):
    class Meta:
        model = FeedPost
        fields = ['image', 'quote', 'hashtags']
        widgets = {
            'quote': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Share a motivational quote...'}),
            'hashtags': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '#fitness #gym #motivation'}),
        }
