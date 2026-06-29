"""Template context values for showing role-specific navbar links."""

from .permissions import is_admin_user, is_coach_user, is_owner_user


def user_roles(request):
    user = request.user
    return {
        'is_owner_role': is_owner_user(user),
        'is_admin_role': is_admin_user(user),
        'is_coach_role': is_coach_user(user),
    }
