"""Views for QAURA Academy.

The heavy business rules live in services.py and permissions.py so views stay small
and future edits are easier.
"""

from datetime import date

from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login as auth_login
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .constants import PLAYER_SESSION_KEY
from .forms import (
    AddSessionsForm,
    PlayerForm,
    PlayerLoginForm,
    PlayerSelfRegistrationForm,
    StaffUserForm,
    ensure_role_groups,
)
from .models import Attendance, Player, TrainingGroup
from .permissions import (
    admin_or_coach_required,
    admin_required,
    is_admin_user,
    is_coach_user,
    owner_required,
)
from .services import add_paid_sessions, mark_player_attendance

User = get_user_model()


def _parse_date(value):
    if not value:
        return timezone.localdate()
    try:
        return date.fromisoformat(value)
    except ValueError:
        return timezone.localdate()


def _role_login_view(request, required_role, template_name, redirect_name, error_message):
    """Shared login handler for admin and coach pages."""
    if request.user.is_authenticated:
        if is_admin_user(request.user):
            return redirect('dashboard')
        if is_coach_user(request.user):
            return redirect('attendance')

    context = {}
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)

        if user is None:
            context['error'] = error_message
        elif required_role == 'admin' and not is_admin_user(user):
            context['error'] = error_message
        elif required_role == 'coach' and not is_coach_user(user):
            context['error'] = error_message
        else:
            auth_login(request, user)
            request.session.pop(PLAYER_SESSION_KEY, None)
            return redirect(redirect_name)

    return render(request, template_name, context)


def admin_login(request):
    return _role_login_view(
        request,
        required_role='admin',
        template_name='registration/admin_login.html',
        redirect_name='dashboard',
        error_message='Invalid admin username or password.',
    )


def coach_login(request):
    return _role_login_view(
        request,
        required_role='coach',
        template_name='registration/coach_login.html',
        redirect_name='attendance',
        error_message='Invalid coach username or password.',
    )


def home_redirect(request):
    """Public role selection page: Player / Coach / Admin."""
    if request.user.is_authenticated:
        if is_admin_user(request.user):
            return redirect('dashboard')
        if is_coach_user(request.user):
            return redirect('attendance')
    if request.session.get(PLAYER_SESSION_KEY):
        return redirect('player_sessions')
    return render(request, 'academy/role_selection.html')


def post_login_redirect(request):
    if request.user.is_authenticated:
        if is_admin_user(request.user):
            return redirect('dashboard')
        if is_coach_user(request.user):
            return redirect('attendance')
    if request.session.get(PLAYER_SESSION_KEY):
        return redirect('player_sessions')
    return redirect('admin_login')


def player_portal(request):
    """Public player entry page. It only shows player register/login options."""
    if is_admin_user(request.user):
        return redirect('dashboard')
    if is_coach_user(request.user):
        return redirect('attendance')
    if request.session.get(PLAYER_SESSION_KEY):
        return redirect('player_sessions')
    return render(request, 'academy/player_portal.html')


def player_login(request):
    if is_admin_user(request.user):
        return redirect('dashboard')
    if is_coach_user(request.user):
        return redirect('attendance')
    if request.session.get(PLAYER_SESSION_KEY):
        return redirect('player_sessions')

    form = PlayerLoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        code = form.cleaned_data['player_code']
        player = Player.objects.filter(player_id=code, is_active=True).first()
        if not player:
            form.add_error('player_code', 'No active player found with this code.')
        else:
            request.session[PLAYER_SESSION_KEY] = player.id
            request.session.modified = True
            return redirect('player_sessions')

    return render(request, 'academy/player_login.html', {'form': form})


def player_self_register(request):
    if request.user.is_authenticated:
        return redirect('post_login_redirect')
    if request.session.get(PLAYER_SESSION_KEY):
        return redirect('player_sessions')

    if request.method == 'POST':
        form = PlayerSelfRegistrationForm(request.POST)
        if form.is_valid():
            player = form.save()
            request.session[PLAYER_SESSION_KEY] = player.id
            request.session.modified = True
            messages.success(
                request,
                f'Registration successful. Your unique player code is {player.player_id}. Save this code. You will use this code only to login as a player.'
            )
            return redirect('player_sessions')
    else:
        form = PlayerSelfRegistrationForm()

    return render(request, 'academy/player_register.html', {'form': form})


def player_sessions(request):
    if is_admin_user(request.user):
        return redirect('dashboard')
    if is_coach_user(request.user):
        return redirect('attendance')

    player_id = request.session.get(PLAYER_SESSION_KEY)
    player = None

    if player_id:
        player = Player.objects.select_related('group').filter(pk=player_id, is_active=True).first()

    # Support old player accounts that may still be authenticated from earlier versions.
    if not player and request.user.is_authenticated:
        player = getattr(request.user, 'player_profile', None)

    if not player:
        request.session.pop(PLAYER_SESSION_KEY, None)
        messages.error(request, 'Please enter your player code to check your sessions.')
        return redirect('player_login')

    request.session[PLAYER_SESSION_KEY] = player.id
    player.used_sessions = max(player.total_sessions - player.remaining_sessions, 0)
    return render(request, 'academy/player_sessions.html', {'player': player})


def player_logout(request):
    request.session.pop(PLAYER_SESSION_KEY, None)
    messages.success(request, 'You logged out from the player page.')
    return redirect('player_portal')


@admin_required
def dashboard(request):
    total_players = Player.objects.count()
    active_players = Player.objects.filter(is_active=True).count()
    zero_sessions = Player.objects.filter(remaining_sessions=0).count()
    groups = TrainingGroup.objects.annotate(players_count=Count('players')).order_by('name')
    latest_attendance = Attendance.objects.select_related('player', 'group').order_by('-created_at')[:8]

    context = {
        'total_players': total_players,
        'active_players': active_players,
        'zero_sessions': zero_sessions,
        'groups': groups,
        'latest_attendance': latest_attendance,
    }
    return render(request, 'academy/dashboard.html', context)


@admin_required
def player_list(request):
    search = request.GET.get('search', '').strip()
    group_id = request.GET.get('group', '').strip()

    players = Player.objects.select_related('group', 'user').all()

    if search:
        players = players.filter(
            Q(name__icontains=search)
            | Q(player_id__icontains=search)
            | Q(phone_number__icontains=search)
            | Q(user__username__icontains=search)
        )

    if group_id:
        players = players.filter(group_id=group_id)

    context = {
        'players': players,
        'groups': TrainingGroup.objects.all(),
        'search': search,
        'selected_group': group_id,
    }
    return render(request, 'academy/player_list.html', context)


@admin_required
def player_create(request):
    if request.method == 'POST':
        form = PlayerForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Player added successfully.')
            return redirect('add_sessions_list')
    else:
        form = PlayerForm(initial={'is_active': True})

    return render(request, 'academy/player_form.html', {'form': form, 'title': 'Add Player'})


@admin_required
def player_update(request, pk):
    player = get_object_or_404(Player, pk=pk)

    if request.method == 'POST':
        form = PlayerForm(request.POST, instance=player)
        if form.is_valid():
            form.save()
            messages.success(request, 'Player updated successfully.')
            return redirect('add_sessions_list')
    else:
        form = PlayerForm(instance=player)

    return render(request, 'academy/player_form.html', {'form': form, 'title': 'Edit Player'})


@admin_required
def player_add_sessions(request, pk):
    player = get_object_or_404(Player, pk=pk)

    if request.method == 'POST':
        form = AddSessionsForm(request.POST)
        if form.is_valid():
            sessions_to_add = form.cleaned_data['sessions_to_add']
            selected_start_date = form.cleaned_data['start_date']
            player = add_paid_sessions(player, sessions_to_add, selected_start_date)
            messages.success(
                request,
                f'{sessions_to_add} weekly sessions added to {player.name}. Paid amount: {player.current_plan_paid_amount} EGP. First session: {player.plan_first_session_date.strftime("%d/%m/%Y")}.',
            )
            return redirect('add_sessions_list')
    else:
        form = AddSessionsForm()

    return render(request, 'academy/add_sessions.html', {'form': form, 'player': player})


@admin_required
def player_delete(request, pk):
    player = get_object_or_404(Player, pk=pk)

    if request.method == 'POST':
        linked_user = player.user
        player.delete()
        if linked_user:
            linked_user.delete()
        messages.success(request, 'Player and linked player user deleted successfully.')
        return redirect('add_sessions_list')

    return render(request, 'academy/player_confirm_delete.html', {'player': player})


@owner_required
def staff_user_list(request):
    ensure_role_groups()
    users = User.objects.filter(is_staff=True, is_superuser=False).prefetch_related('groups').order_by('username')
    return render(request, 'academy/staff_user_list.html', {'users': users})


@owner_required
def staff_user_create(request):
    if request.method == 'POST':
        form = StaffUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Account "{user.username}" created successfully.')
            return redirect('staff_user_list')
    else:
        form = StaffUserForm()
    return render(request, 'academy/staff_user_form.html', {'form': form})


@owner_required
def staff_user_delete(request, pk):
    user = get_object_or_404(User, pk=pk, is_staff=True, is_superuser=False)
    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f'Account "{username}" deleted successfully.')
        return redirect('staff_user_list')
    return render(request, 'academy/staff_user_confirm_delete.html', {'staff_user': user})


@admin_or_coach_required
def attendance_page(request):
    groups = TrainingGroup.objects.all()
    selected_group_id = request.GET.get('group') or request.POST.get('group')
    selected_date = _parse_date(request.GET.get('date') or request.POST.get('date'))

    if not selected_group_id and groups.exists():
        selected_group_id = groups.first().id

    selected_group = None
    players = Player.objects.none()
    existing_attendance = {}

    if selected_group_id:
        selected_group = get_object_or_404(TrainingGroup, pk=selected_group_id)
        players = Player.objects.filter(group=selected_group, is_active=True).order_by('name')
        records = Attendance.objects.filter(date=selected_date, player__in=players)
        existing_attendance = {record.player_id: record.status for record in records}

    if request.method == 'POST':
        player_id = request.POST.get('player_id')
        status = request.POST.get('status')
        player = get_object_or_404(Player, pk=player_id, group=selected_group)
        result = mark_player_attendance(player, selected_date, status, request.user)
        getattr(messages, result['level'])(request, result['message'])
        return redirect(f'{reverse("attendance")}?group={selected_group_id}&date={selected_date}')

    attendance_rows = [
        {'player': player, 'status': existing_attendance.get(player.id)}
        for player in players
    ]

    context = {
        'groups': groups,
        'selected_group': selected_group,
        'selected_group_id': str(selected_group_id) if selected_group_id else '',
        'selected_date': selected_date,
        'attendance_rows': attendance_rows,
    }
    return render(request, 'academy/attendance.html', context)


@admin_required
def attendance_history(request):
    group_id = request.GET.get('group', '').strip()
    date_value = request.GET.get('date', '').strip()

    records = Attendance.objects.select_related('player', 'group', 'created_by').all()

    if group_id:
        records = records.filter(group_id=group_id)

    if date_value:
        records = records.filter(date=_parse_date(date_value))

    context = {
        'records': records,
        'groups': TrainingGroup.objects.all(),
        'selected_group': group_id,
        'selected_date': date_value,
    }
    return render(request, 'academy/history.html', context)
