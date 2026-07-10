"""Business logic for player codes, paid sessions, and attendance.

Keeping this logic outside views makes future edits safer. For example:
- change numeric code generation here
- change package pricing in constants.py
- change attendance deduction rules here
- change session-date calculation here
"""

from datetime import timedelta

from django.db import transaction


from .constants import FIRST_PLAYER_CODE
from .models import Attendance, Player, SessionPayment


GROUP_DAY_TO_WEEKDAY = {
    'Monday': 0,
    'Tuesday': 1,
    'Wednesday': 2,
    'Thursday': 3,
    'Friday': 4,
    'Saturday': 5,
    'Sunday': 6,
}


def get_group_weekday(group):
    """Return the Python weekday number for a training group."""
    if not group:
        return None

    return GROUP_DAY_TO_WEEKDAY.get(group.day)


def generate_unique_player_code():
    """
    Generate the smallest available numeric player code starting from 100.

    Example:
    Existing codes: 100, 101, 102
    If player 101 is deleted, the next created player gets 101 again.
    """
    used_codes = set()

    for code in Player.objects.values_list('player_id', flat=True):
        if code and str(code).isdigit():
            used_codes.add(int(code))

    next_code = FIRST_PLAYER_CODE

    while next_code in used_codes:
        next_code += 1

    return str(next_code)


def calculate_session_dates(start_date, sessions_count, groups):
    """
    Calculate planned session dates.

    If player is in one group, dates follow that group weekly.
    If player is in both groups, dates follow both group days chronologically.

    Example:
    Groups: Monday + Saturday
    Sessions: 4
    Dates: Monday, Saturday, Monday, Saturday
    """
    sessions_count = int(sessions_count or 0)

    if not start_date or sessions_count <= 0:
        return []

    if not isinstance(groups, (list, tuple)):
        groups = [groups]

    weekdays = sorted({
        get_group_weekday(group)
        for group in groups
        if group and get_group_weekday(group) is not None
    })

    if not weekdays:
        return []

    session_dates = []
    current_date = start_date

    while len(session_dates) < sessions_count:
        if current_date.weekday() in weekdays:
            session_dates.append(current_date)

        current_date += timedelta(days=1)

    return session_dates


def calculate_weekly_plan_dates(player, selected_start_date, sessions_count):
    """
    Return first session, end date, and all planned dates for a player.

    If the player is registered in one group:
    - Dates follow that group day weekly.

    If the player is registered in both groups:
    - Dates alternate chronologically between the selected group days.
    """
    sessions_count = int(sessions_count or 0)

    if not selected_start_date or sessions_count <= 0:
        return None, None, []

    session_dates = calculate_session_dates(
        selected_start_date,
        sessions_count,
        player.enrolled_groups,
    )

    first_session_date = session_dates[0] if session_dates else None
    end_date = session_dates[-1] if session_dates else None

    return first_session_date, end_date, session_dates

def calculate_paid_amount(sessions_count):
    """
    Calculate paid amount automatically.
    4 sessions = 1500 EGP
    """
    sessions_count = int(sessions_count or 0)
    return int(sessions_count * Player.PRICE_PER_SESSION)


def add_paid_sessions(player, sessions_to_add, selected_start_date, created_by=None):
    """
    Add paid sessions, restart the current plan, and save income record.

    Example:
    4 sessions = 1500 EGP
    8 sessions = 3000 EGP
    """
    sessions_to_add = int(sessions_to_add or 0)

    first_session_date, end_date, _ = calculate_weekly_plan_dates(
        player,
        selected_start_date,
        sessions_to_add,
    )

    paid_amount = calculate_paid_amount(sessions_to_add)

    with transaction.atomic():
        player.total_sessions += sessions_to_add
        player.remaining_sessions = sessions_to_add
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

        SessionPayment.objects.create(
            player=player,
            sessions_count=sessions_to_add,
            amount_egp=paid_amount,
            created_by=created_by,
        )

    return player


def count_used_sessions_in_current_plan(player):
    """
    Count how many planned sessions have attend/absent records.

    Only current plan dates are counted.
    Old attendance records outside the current plan do not affect remaining sessions.
    """
    session_dates = player.plan_session_dates

    if not session_dates:
        return 0

    return Attendance.objects.filter(
        player=player,
        date__in=session_dates,
        status__in=[Attendance.ATTEND, Attendance.ABSENT],
    ).count()


def sync_remaining_sessions_with_current_plan(player):
    """
    Make remaining sessions match the current plan attendance records.

    Example:
    plan_sessions_count = 8
    used sessions = 1
    remaining = 7
    """
    used_sessions = count_used_sessions_in_current_plan(player)
    plan_sessions_count = player.plan_sessions_count or 0

    player.remaining_sessions = max(plan_sessions_count - used_sessions, 0)
    player.save(update_fields=['remaining_sessions', 'updated_at'])

    return player.remaining_sessions


def mark_player_attendance(player, selected_date, status, created_by, selected_group=None):
    """
    Create/update attendance and safely adjust remaining sessions.

    Rule:
    - Attend deducts one session.
    - Absent also deducts one session.
    - Changing Attend to Absent does not deduct again.
    - Changing Absent to Attend does not deduct again.
    - Same player/date can only consume one session once.
    - Attendance is only allowed on planned session dates.
    - If player is registered in both groups, attendance is only allowed
      for the selected group's correct weekday.
    """
    if status not in [Attendance.ATTEND, Attendance.ABSENT]:
        return {
            'level': 'error',
            'message': 'Invalid attendance status.',
            'player': player,
        }

    if not selected_date:
        return {
            'level': 'error',
            'message': 'Please select a valid session date.',
            'player': player,
        }

    with transaction.atomic():
        locked_player = Player.objects.select_for_update().select_related(
            'group',
            'secondary_group',
        ).get(pk=player.pk)

        attendance_group = selected_group or locked_player.group

        if attendance_group not in locked_player.enrolled_groups:
            return {
                'level': 'error',
                'message': f'{locked_player.name} is not registered in this group.',
                'player': locked_player,
            }

        session_dates = locked_player.plan_session_dates

        if session_dates and selected_date not in session_dates:
            return {
                'level': 'error',
                'message': f'{locked_player.name} does not have a planned session on this date.',
                'player': locked_player,
            }

        group_weekday = get_group_weekday(attendance_group)

        if group_weekday is not None and selected_date.weekday() != group_weekday:
            return {
                'level': 'error',
                'message': f'{locked_player.name} does not have a {attendance_group.name} session on this date.',
                'player': locked_player,
            }

        sync_remaining_sessions_with_current_plan(locked_player)
        locked_player.refresh_from_db()

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

        if old_status is None:
            if locked_player.remaining_sessions <= 0:
                return {
                    'level': 'error',
                    'message': f'{locked_player.name} has no remaining sessions.',
                    'player': locked_player,
                }

            Attendance.objects.create(
                player=locked_player,
                group=attendance_group,
                date=selected_date,
                status=status,
                created_by=created_by,
            )

            sync_remaining_sessions_with_current_plan(locked_player)
            locked_player.refresh_from_db()

            return {
                'level': 'success',
                'message': f'{locked_player.name} marked as {status}. One session was used.',
                'player': locked_player,
            }

        attendance.status = status
        attendance.group = attendance_group
        attendance.created_by = created_by
        attendance.save(update_fields=['status', 'group', 'created_by', 'updated_at'])

        sync_remaining_sessions_with_current_plan(locked_player)
        locked_player.refresh_from_db()

    return {
        'level': 'success',
        'message': f'{locked_player.name} updated to {status}. Session count was not changed again.',
        'player': locked_player,
    }


def get_player_session_progress(player):
    """
    Return the current plan sessions with attendance status.

    Example output:
    [
        {'number': 1, 'date': date, 'status': 'attend'},
        {'number': 2, 'date': date, 'status': 'absent'},
        {'number': 3, 'date': date, 'status': None},
    ]
    """
    session_dates = player.plan_session_dates

    if not session_dates:
        return []

    attendance_records = Attendance.objects.filter(
        player=player,
        date__in=session_dates,
    )

    attendance_by_date = {
        record.date: record.status
        for record in attendance_records
    }

    return [
        {
            'number': index + 1,
            'date': session_date,
            'status': attendance_by_date.get(session_date),
        }
        for index, session_date in enumerate(session_dates)
    ]