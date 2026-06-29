"""Business logic for player codes, paid sessions, and attendance.

Keeping this logic outside views makes future edits safer. For example:
- change numeric code generation here
- change package pricing in constants.py
- change attendance deduction rules here
"""

from datetime import timedelta

from django.db import transaction

from .constants import FIRST_PLAYER_CODE
from .models import Attendance, Player


def generate_unique_player_code():
    """Generate numeric player codes: 100, 101, 102..."""
    numeric_codes = []
    for code in Player.objects.values_list('player_id', flat=True):
        if code and str(code).isdigit():
            numeric_codes.append(int(code))
    next_code = max(numeric_codes, default=FIRST_PLAYER_CODE - 1) + 1
    return str(next_code)


def calculate_weekly_plan_dates(player, selected_start_date, sessions_count):
    """Return first session, end date, and all weekly dates for a player's group."""
    sessions_count = int(sessions_count or 0)
    if not selected_start_date or sessions_count <= 0:
        return None, None, []

    first_session_date = Player.align_date_to_weekday(selected_start_date, player.group.day)
    session_dates = [first_session_date + timedelta(days=7 * index) for index in range(sessions_count)]
    end_date = session_dates[-1] if session_dates else None
    return first_session_date, end_date, session_dates


def add_paid_sessions(player, sessions_to_add, selected_start_date):
    """Add paid sessions and restart the displayed weekly plan dates."""
    sessions_to_add = int(sessions_to_add)
    first_session_date, end_date, _ = calculate_weekly_plan_dates(
        player,
        selected_start_date,
        sessions_to_add,
    )

    player.total_sessions += sessions_to_add
    player.remaining_sessions += sessions_to_add
    player.plan_start_date = first_session_date
    player.plan_sessions_count = sessions_to_add
    player.plan_end_date_manual = end_date
    player.save(update_fields=[
        'total_sessions',
        'remaining_sessions',
        'plan_start_date',
        'plan_end_date_manual',
        'plan_sessions_count',
        'updated_at',
    ])
    return player


def mark_player_attendance(player, selected_date, status, created_by):
    """Create/update attendance and safely adjust remaining sessions.

    Returns a dict with: level, message, player.
    """
    if status not in [Attendance.ATTEND, Attendance.ABSENT]:
        return {'level': 'error', 'message': 'Invalid attendance status.', 'player': player}

    with transaction.atomic():
        locked_player = Player.objects.select_for_update().select_related('group').get(pk=player.pk)
        attendance = Attendance.objects.select_for_update().filter(
            player=locked_player,
            date=selected_date,
        ).first()

        old_status = attendance.status if attendance else None

        if old_status == status:
            return {
                'level': 'info',
                'message': f'{locked_player.name} is already marked as {status}.',
                'player': locked_player,
            }

        if old_status == Attendance.ATTEND and status == Attendance.ABSENT:
            locked_player.remaining_sessions += 1
        elif old_status in [None, Attendance.ABSENT] and status == Attendance.ATTEND:
            if locked_player.remaining_sessions <= 0:
                return {
                    'level': 'error',
                    'message': f'{locked_player.name} has no remaining sessions.',
                    'player': locked_player,
                }
            locked_player.remaining_sessions -= 1

        locked_player.save(update_fields=['remaining_sessions', 'updated_at'])

        if attendance:
            attendance.status = status
            attendance.group = locked_player.group
            attendance.created_by = created_by
            attendance.save(update_fields=['status', 'group', 'created_by', 'updated_at'])
        else:
            Attendance.objects.create(
                player=locked_player,
                group=locked_player.group,
                date=selected_date,
                status=status,
                created_by=created_by,
            )

    return {
        'level': 'success',
        'message': f'{locked_player.name} marked as {status}.',
        'player': locked_player,
    }
