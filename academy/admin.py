from django.contrib import admin

from .models import Attendance, Player, SessionPayment, TrainingGroup


@admin.register(TrainingGroup)
class TrainingGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'day', 'time')
    search_fields = ('name', 'day')


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = (
        'player_id',
        'name',
        'phone_number',
        'username',
        'display_groups',
        'total_sessions',
        'remaining_sessions',
        'plan_start_date',
        'display_plan_end_date',
        'is_active',
    )
    list_filter = ('group', 'secondary_group', 'is_active')
    search_fields = ('player_id', 'name', 'phone_number', 'user__username')

    def username(self, obj):
        return obj.user.username if obj.user else '-'
    username.short_description = 'Username'

    def display_groups(self, obj):
        return obj.group_display
    display_groups.short_description = 'Groups'

    def display_plan_end_date(self, obj):
        return obj.plan_end_date or '-'
    display_plan_end_date.short_description = 'End date'


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('date', 'player', 'group', 'status', 'created_by')
    list_filter = ('date', 'group', 'status')
    search_fields = ('player__player_id', 'player__name')


@admin.register(SessionPayment)
class SessionPaymentAdmin(admin.ModelAdmin):
    list_display = (
        'created_at',
        'player',
        'player_code',
        'sessions_count',
        'amount_egp',
        'created_by',
    )
    list_filter = ('created_at', 'created_by')
    search_fields = (
        'player__player_id',
        'player__name',
        'created_by__username',
    )
    readonly_fields = ('created_at',)

    def player_code(self, obj):
        return obj.player.player_id if obj.player else '-'
    player_code.short_description = 'Player Code'