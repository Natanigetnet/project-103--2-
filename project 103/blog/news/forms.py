from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import RegexValidator
from .models import Category, UserProfile, names


ethiopian_phone_validator = RegexValidator(
    regex=r'^(?:\+251|0)[1-9]\d{8}$',
    message='Phone number must be a valid Ethiopian format (e.g. +251912345678 or 0912345678).',
)


class TraineeAccountForm(forms.Form):
    full_name = forms.CharField(max_length=40, label='Full name')
    email = forms.EmailField(label='Email address')
    phone_number = forms.CharField(max_length=20, label='Phone number', required=False, validators=[ethiopian_phone_validator])
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

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            email = email.strip().lower()
            user_qs = User.objects.filter(email__iexact=email)
            if self.exclude_user:
                user_qs = user_qs.exclude(id=self.exclude_user.id)
            if user_qs.exists():
                raise forms.ValidationError('A user with this email address already exists.')
            names_qs = names.objects.filter(email__iexact=email)
            if self.exclude_user:
                own_names = names.objects.filter(trainer=self.exclude_user)
                names_qs = names_qs.exclude(id__in=own_names.values_list('id', flat=True))
            if names_qs.exists():
                raise forms.ValidationError('A member with this email address already exists.')
        return email

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if phone:
            phone = phone.strip()
            names_qs = names.objects.filter(phone_number=phone)
            if self.exclude_user:
                names_qs = names_qs.exclude(trainer=self.exclude_user)
            if names_qs.exists():
                raise forms.ValidationError('A member with this phone number already exists.')
        return phone


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
    phone_number = forms.CharField(max_length=20, label='Phone number', required=False, validators=[ethiopian_phone_validator])
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
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.TextInput) or isinstance(field.widget, forms.EmailInput):
                field.widget.attrs.setdefault('class', 'form-control')
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.setdefault('class', 'form-select')
            elif isinstance(field.widget, forms.PasswordInput):
                field.widget.attrs.setdefault('class', 'form-control')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            email = email.strip().lower()
            if User.objects.filter(email__iexact=email).exists():
                raise forms.ValidationError('A user with this email address already exists.')
            if names.objects.filter(email__iexact=email).exists():
                raise forms.ValidationError('A member with this email address already exists.')
        return email

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if phone:
            phone = phone.strip()
            if names.objects.filter(phone_number=phone).exists():
                raise forms.ValidationError('A member with this phone number already exists.')
        return phone

    def clean_role(self):
        role = self.cleaned_data.get('role')
        if role not in ('trainer', 'trainee', None):
            return 'trainee'
        return role

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data.get('email', '')
        if commit:
            user.save()
        return user

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        category = cleaned_data.get('category')
        if role == 'trainer' and category is None:
            self.add_error('category', 'Trainer category is required when registering a trainer.')
        if self.fields['full_name'].required and not cleaned_data.get('full_name', '').strip():
            self.add_error('full_name', 'Full name is required.')
        if self.fields['phone_number'].required and not cleaned_data.get('phone_number', '').strip():
            self.add_error('phone_number', 'Phone number is required.')
        return cleaned_data
