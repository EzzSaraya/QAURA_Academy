"""Role helpers and view guards.

Owner = Django superuser.
Admin = staff user in QAURA Admins group, or owner.
Coach = staff user that is not an admin.
Player = public session-based login using numeric player code.
"""

from functools import wraps

from django.contrib import messages
from django.contrib.auth.models import Group
from django.shortcuts import redirect

from .constants import ADMIN_GROUP_NAME, COACH_GROUP_NAME, PLAYER_SESSION_KEY


def ensure_role_groups():
    """Create and return the Admin and Coach groups."""
    admin_group, _ = Group.objects.get_or_create(name=ADMIN_GROUP_NAME)
    coach_group, _ = Group.objects.get_or_create(name=COACH_GROUP_NAME)
    return admin_group, coach_group


def user_in_group(user, group_name):
    if not user.is_authenticated:
        return False
    return user.groups.filter(name=group_name).exists()


def is_owner_user(user):
    return user.is_authenticated and user.is_active and user.is_superuser


def is_admin_user(user):
    return (
        user.is_authenticated
        and user.is_active
        and (user.is_superuser or (user.is_staff and user_in_group(user, ADMIN_GROUP_NAME)))
    )


def is_coach_user(user):
    return user.is_authenticated and user.is_active and user.is_staff and not is_admin_user(user)


def is_admin_or_coach_user(user):
    return is_admin_user(user) or is_coach_user(user)


def admin_required(view_func):
    """Allow only admins/owners to access admin pages."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if is_admin_user(request.user):
            return view_func(request, *args, **kwargs)
        if is_coach_user(request.user):
            messages.error(request, 'Coach accounts can only take attendance.')
            return redirect('attendance')
        if request.session.get(PLAYER_SESSION_KEY):
            return redirect('player_sessions')
        return redirect('admin_login')
    return wrapper


def owner_required(view_func):
    """Allow only the owner/superuser to manage admin and coach accounts."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if is_owner_user(request.user):
            return view_func(request, *args, **kwargs)
        if is_admin_user(request.user):
            messages.error(request, 'Only the owner can manage admin and coach accounts.')
            return redirect('dashboard')
        if is_coach_user(request.user):
            return redirect('attendance')
        return redirect('admin_login')
    return wrapper


def admin_or_coach_required(view_func):
    """Allow admins and coaches to take attendance."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if is_admin_or_coach_user(request.user):
            return view_func(request, *args, **kwargs)
        if request.session.get(PLAYER_SESSION_KEY):
            return redirect('player_sessions')
        return redirect('coach_login')
    return wrapper
