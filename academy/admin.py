from django.contrib import admin
from .models import Attendance, Player, TrainingGroup


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
        'group',
        'total_sessions',
        'remaining_sessions',
        'plan_start_date',
        'display_plan_end_date',
        'is_active',
    )
    list_filter = ('group', 'is_active')
    search_fields = ('player_id', 'name', 'phone_number', 'user__username')

    def display_plan_end_date(self, obj):
        return obj.plan_end_date or '-'
    display_plan_end_date.short_description = 'End date'

    def username(self, obj):
        return obj.user.username if obj.user else '-'


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('date', 'player', 'group', 'status', 'created_by')
    list_filter = ('date', 'group', 'status')
    search_fields = ('player__player_id', 'player__name')
