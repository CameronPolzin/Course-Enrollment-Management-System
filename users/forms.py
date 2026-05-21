from django import forms
from .models import User
from django.contrib.auth.forms import UserCreationForm

class UserRegistrationForm(UserCreationForm):

    first_name = forms.CharField(
        max_length=30,
        help_text="",
        widget=forms.TextInput(attrs={
            'placeholder': 'First Name',
            'class': 'full-width-input'
        })
    )

    last_name = forms.CharField(
        max_length=30,
        help_text="",
        widget=forms.TextInput(attrs={
            'placeholder': 'Last Name',
            'class': 'full-width-input'
        })
    )

    username = forms.CharField(
        max_length=30,
        help_text="",
        widget=forms.TextInput(attrs={
            'placeholder': 'Username',
            'class': 'full-width-input'
        })
    )

    password1 = forms.CharField(
        label="Password",
        help_text="",
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Password',
            'class': 'full-width-input'
        })
    )

    password2 = forms.CharField(
        label="Confirm Password",
        help_text="",
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Confirm Password',
            'class': 'full-width-input'
        })
    )

    role = forms.ChoiceField(
        choices=User.ROLE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'full-width-input'
        })
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'password1', 'password2', 'role']