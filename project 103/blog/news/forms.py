from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Category, UserProfile, names, FeedPost


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
        email = self.cleaned_data['email'].strip()
        if User.objects.filter(email__iexact=email).exists() or names.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email address already exists.')
        return email

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number', '').strip()
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
