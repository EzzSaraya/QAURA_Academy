"""Forms for player, paid-session, and staff-user workflows."""

import code

from django import forms
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from .constants import (
    ADMIN_GROUP_NAME,
    COACH_GROUP_NAME,
    SESSION_PACKAGE_CHOICES,
)
from .models import Player, TrainingGroup
from .permissions import ensure_role_groups
from .services import calculate_weekly_plan_dates, generate_unique_player_code


User = get_user_model()


class PlayerForm(forms.ModelForm):
    """Admin form for editing player details and automatic plan dates."""

    username = forms.CharField(
        label='Username',
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Player username',
        })
    )

    class Meta:
        model = Player
        fields = [
            'player_id',
            'name',
            'phone_number',
            'username',
            'group',
            'total_sessions',
            'remaining_sessions',
            'plan_start_date',
            'plan_end_date_manual',
            'plan_sessions_count',
            'is_active',
        ]
        labels = {
            'player_id': 'Player Code',
            'phone_number': 'Phone Number',
            'plan_start_date': 'Start Date',
            'plan_end_date_manual': 'End Date (Auto)',
            'plan_sessions_count': 'Current Plan Sessions',
        }
        widgets = {
            'player_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Example: 100'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Player full name'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Example: 01000000000'}),
            'group': forms.Select(attrs={'class': 'form-select'}),
            'total_sessions': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'remaining_sessions': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'plan_start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'plan_end_date_manual': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'plan_sessions_count': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Player codes are generated automatically by the system.
        self.fields['player_id'].required = False
        self.fields['player_id'].disabled = True
        self.fields['player_id'].help_text = (
        'Generated automatically. If a player is deleted, their code becomes available again.'
        )

        if not (self.instance and self.instance.pk):
            self.fields['player_id'].initial = 'Auto generated'
        self.fields['plan_end_date_manual'].disabled = True
        self.fields['plan_end_date_manual'].help_text = (
            'End date is calculated automatically from start date, group day, and current plan sessions.'
        )
        if self.instance and self.instance.pk and self.instance.user:
            self.fields['username'].initial = self.instance.user.username
    def clean_player_id(self):
        code = self.cleaned_data.get('player_id', '')

        if code == 'Auto generated':
            return ''

        return str(code).strip()

    def clean_phone_number(self):
        return self.cleaned_data.get('phone_number', '').strip()

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        current_user_id = self.instance.user_id if self.instance and self.instance.pk else None
        query = User.objects.filter(username__iexact=username)
        if current_user_id:
            query = query.exclude(pk=current_user_id)
        if query.exists():
            raise forms.ValidationError('This username is already used. Please choose another one.')
        return username

    def clean(self):
        cleaned_data = super().clean()
        total_sessions = cleaned_data.get('total_sessions')
        remaining_sessions = cleaned_data.get('remaining_sessions')
        plan_start_date = cleaned_data.get('plan_start_date')
        plan_sessions_count = cleaned_data.get('plan_sessions_count') or 0
        group = cleaned_data.get('group')

        if total_sessions is not None and remaining_sessions is not None:
            if remaining_sessions > total_sessions:
                raise forms.ValidationError('Remaining sessions cannot be more than total sessions.')

        if plan_start_date and plan_sessions_count > 0 and group:
            # Use a temporary player-like object so the shared service can align to the group day.
            temp_player = self.instance if self.instance and self.instance.pk else Player(group=group)
            temp_player.group = group
            first_session_date, end_date, _ = calculate_weekly_plan_dates(
                temp_player,
                plan_start_date,
                plan_sessions_count,
            )
            cleaned_data['plan_start_date'] = first_session_date
            cleaned_data['plan_end_date_manual'] = end_date
        elif not plan_start_date or plan_sessions_count <= 0:
            cleaned_data['plan_end_date_manual'] = None

        return cleaned_data

    def save(self, commit=True):
        player = super().save(commit=False)
        username = self.cleaned_data['username']
        if not player.player_id or player.player_id == 'Auto generated':
            player.player_id = generate_unique_player_code()

        with transaction.atomic():
            if player.user:
                user = player.user
                user.username = username
                user.first_name = player.name
                if commit:
                    user.save(update_fields=['username', 'first_name'])
            else:
                user = User(username=username, first_name=player.name, is_staff=False, is_superuser=False)
                user.set_unusable_password()
                if commit:
                    user.save()
                player.user = user

            player.plan_start_date = self.cleaned_data.get('plan_start_date')
            player.plan_end_date_manual = self.cleaned_data.get('plan_end_date_manual')

            if commit:
                player.save()
                self.save_m2m()
        return player


class AddSessionsForm(forms.Form):
    sessions_to_add = forms.ChoiceField(
        label='Number of sessions paid',
        choices=SESSION_PACKAGE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_sessions_to_add',
        })
    )
    start_date = forms.DateField(
        label='Start date',
        initial=timezone.localdate,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
        })
    )

    def clean_sessions_to_add(self):
        sessions = int(self.cleaned_data['sessions_to_add'])
        if sessions % Player.SESSIONS_PER_PACKAGE != 0:
            raise forms.ValidationError('Sessions must be selected in packages of 4.')
        return sessions


class PlayerLoginForm(forms.Form):
    player_code = forms.CharField(
        label='Player Code',
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control code-box text-center',
            'placeholder': 'Enter your code, example: 100',
            'autocomplete': 'off',
            'autofocus': True,
        })
    )

    def clean_player_code(self):
        code = self.cleaned_data['player_code'].strip()
        if not code.isdigit():
            raise forms.ValidationError('Player code must contain numbers only.')
        return code


class PlayerSelfRegistrationForm(forms.Form):
    name = forms.CharField(
        label='Full Name',
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your full name',
            'autocomplete': 'name',
        })
    )
    phone_number = forms.CharField(
        label='Phone Number',
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your phone number',
            'autocomplete': 'tel',
        })
    )
    username = forms.CharField(
        label='Username',
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Choose a username',
            'autocomplete': 'username',
        })
    )
    group = forms.ModelChoiceField(
        label='Training Group',
        queryset=TrainingGroup.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    def clean_name(self):
        return self.cleaned_data['name'].strip()

    def clean_phone_number(self):
        return self.cleaned_data['phone_number'].strip()

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('This username is already used. Please choose another one.')
        return username

    def save(self):
        with transaction.atomic():
            user = User(
                username=self.cleaned_data['username'],
                first_name=self.cleaned_data['name'],
                is_staff=False,
                is_superuser=False,
            )
            user.set_unusable_password()
            user.save()
            player = Player.objects.create(
                user=user,
                player_id=generate_unique_player_code(),
                name=self.cleaned_data['name'],
                phone_number=self.cleaned_data['phone_number'],
                group=self.cleaned_data['group'],
                total_sessions=0,
                remaining_sessions=0,
                is_active=True,
            )
        return player


class StaffUserForm(forms.Form):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('coach', 'Coach'),
    ]

    full_name = forms.CharField(
        label='Full Name',
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full name'})
    )
    username = forms.CharField(
        label='Username',
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'})
    )
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm password'})
    )
    role = forms.ChoiceField(
        label='Role',
        choices=ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('This username is already used.')
        return username

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Passwords do not match.')
        return cleaned_data

    def save(self):
        admin_group, coach_group = ensure_role_groups()
        role = self.cleaned_data['role']
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            password=self.cleaned_data['password1'],
            first_name=self.cleaned_data.get('full_name', ''),
            is_staff=True,
            is_superuser=False,
        )
        if role == 'admin':
            user.groups.add(admin_group)
        else:
            user.groups.add(coach_group)
        return user


class PlayerSessionLookupForm(forms.Form):
    player_id = forms.CharField(
        label='Player Code',
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your Player Code, example: 100',
            'autocomplete': 'off',
        }),
    )

    def clean_player_id(self):
        return self.cleaned_data['player_id'].strip()
