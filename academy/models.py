from datetime import timedelta

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from . import constants


class TrainingGroup(models.Model):
    name = models.CharField(max_length=100, unique=True)
    day = models.CharField(max_length=20)
    time = models.TimeField()

    class Meta:
        ordering = ['day', 'time']

    def __str__(self):
        return f'{self.name} - {self.day} {self.time.strftime("%I:%M %p")}'


class Player(models.Model):
    PRICE_PER_4_SESSIONS = constants.PRICE_PER_4_SESSIONS
    SESSIONS_PER_PACKAGE = constants.SESSIONS_PER_PACKAGE
    PRICE_PER_SESSION = constants.PRICE_PER_SESSION

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='player_profile',
        null=True,
        blank=True,
        help_text='The login account used by the player.',
    )

    player_id = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Player Code',
    )

    name = models.CharField(max_length=150)

    phone_number = models.CharField(
        max_length=30,
        blank=True,
        default='',
        verbose_name='Phone Number',
    )

    group = models.ForeignKey(
        TrainingGroup,
        on_delete=models.PROTECT,
        related_name='players',
        verbose_name='Primary Group',
    )

    secondary_group = models.ForeignKey(
        TrainingGroup,
        on_delete=models.PROTECT,
        related_name='secondary_players',
        null=True,
        blank=True,
        verbose_name='Secondary Group',
    )

    total_sessions = models.PositiveIntegerField(
        validators=[MinValueValidator(0)],
    )

    remaining_sessions = models.PositiveIntegerField(
        validators=[MinValueValidator(0)],
    )

    plan_start_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Current Plan Start Date',
    )

    plan_end_date_manual = models.DateField(
        null=True,
        blank=True,
        verbose_name='Current Plan End Date',
    )

    plan_sessions_count = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='Current Plan Sessions',
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f'{self.player_id} - {self.name}'

    @staticmethod
    def _weekday_number(day_name):
        """Return Python weekday number for a group day name. Monday=0, Sunday=6."""
        weekdays = {
            'monday': 0,
            'tuesday': 1,
            'wednesday': 2,
            'thursday': 3,
            'friday': 4,
            'saturday': 5,
            'sunday': 6,
        }
        return weekdays.get(str(day_name).strip().lower())

    @staticmethod
    def align_date_to_weekday(start_date, day_name):
        """Move start_date forward to the next date that matches the group day."""
        if not start_date:
            return None

        target_weekday = Player._weekday_number(day_name)

        if target_weekday is None:
            return start_date

        days_until_group_day = (target_weekday - start_date.weekday()) % 7
        return start_date + timedelta(days=days_until_group_day)

    @property
    def enrolled_groups(self):
        """
        Return all groups the player is registered in.

        Example:
        - Monday only
        - Saturday only
        - Monday + Saturday
        """
        groups = []

        if self.group:
            groups.append(self.group)

        if self.secondary_group and self.secondary_group_id != self.group_id:
            groups.append(self.secondary_group)

        return groups

    @property
    def group_display(self):
        """Display one group or both groups nicely in templates."""
        groups = self.enrolled_groups

        if not groups:
            return 'No group'

        return ' + '.join(group.name for group in groups)

    @property
    def plan_session_dates(self):
        """
        Return the current plan session dates.

        If player is in one group:
        dates follow that group weekly.

        If player is in both groups:
        dates follow both group days chronologically.

        Example:
        Monday + Saturday, 4 sessions:
        Monday, Saturday, Monday, Saturday
        """
        if not self.plan_start_date or not self.plan_sessions_count:
            return []

        from .services import calculate_session_dates

        return calculate_session_dates(
            self.plan_start_date,
            self.plan_sessions_count,
            self.enrolled_groups,
        )

    @property
    def plan_first_session_date(self):
        """The first actual session date in the current plan."""
        session_dates = self.plan_session_dates

        if not session_dates:
            return None

        return session_dates[0]

    @property
    def computed_plan_end_date(self):
        """The last actual session date in the current plan."""
        session_dates = self.plan_session_dates

        if not session_dates:
            return None

        return session_dates[-1]

    @property
    def plan_end_date(self):
        """Return manually saved end date, or calculate it if missing."""
        return self.plan_end_date_manual or self.computed_plan_end_date

    @property
    def current_plan_paid_amount(self):
        """
        Calculate paid amount automatically from the current plan sessions.

        Example:
        4 sessions = 1500 EGP
        8 sessions = 3000 EGP
        """
        sessions_count = self.plan_sessions_count or 0
        return sessions_count * self.PRICE_PER_SESSION

    @property
    def total_paid_amount(self):
        """Calculate total paid amount from all total sessions."""
        return self.total_sessions * self.PRICE_PER_SESSION



class SessionPayment(models.Model):
    player = models.ForeignKey(
        Player,
        on_delete=models.CASCADE,
        related_name='session_payments',
    )

    sessions_count = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
    )

    amount_egp = models.PositiveIntegerField(
        validators=[MinValueValidator(0)],
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_session_payments',
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.player.name} - {self.sessions_count} sessions - {self.amount_egp} EGP'









class Attendance(models.Model):
    ATTEND = 'attend'
    ABSENT = 'absent'

    STATUS_CHOICES = [
        (ATTEND, 'Attend'),
        (ABSENT, 'Absent'),
    ]

    player = models.ForeignKey(
        Player,
        on_delete=models.CASCADE,
        related_name='attendance_records',
    )

    group = models.ForeignKey(
        TrainingGroup,
        on_delete=models.PROTECT,
        related_name='attendance_records',
    )

    date = models.DateField(default=timezone.localdate)

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', 'player__name']
        constraints = [
            models.UniqueConstraint(
                fields=['player', 'date'],
                name='one_attendance_per_player_per_day',
            )
        ]

    def __str__(self):
        return f'{self.player.name} - {self.date} - {self.status}'