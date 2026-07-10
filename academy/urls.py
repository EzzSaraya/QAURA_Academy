from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_redirect, name='home'),
    path('after-login/', views.post_login_redirect, name='post_login_redirect'),
    path('player/', views.player_portal, name='player_portal'),
    path('player-login/', views.player_login, name='player_login'),
    path('player-logout/', views.player_logout, name='player_logout'),
    path('register/', views.player_self_register, name='player_self_register'),
    path('my-sessions/', views.player_sessions, name='player_sessions'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('players/', views.player_list, name='player_list'),
    path('add-sessions/', views.player_list, name='add_sessions_list'),
    path('players/add/', views.player_create, name='player_create'),
    path('players/<int:pk>/edit/', views.player_update, name='player_update'),
    path('players/<int:pk>/add-sessions/', views.player_add_sessions, name='player_add_sessions'),
    path('players/<int:pk>/delete/', views.player_delete, name='player_delete'),
    path('owner/users/', views.staff_user_list, name='staff_user_list'),
    path('owner/users/create/', views.staff_user_create, name='staff_user_create'),
    path('owner/users/<int:pk>/delete/', views.staff_user_delete, name='staff_user_delete'),
    path('attendance/', views.attendance_page, name='attendance'),
    path('history/', views.attendance_history, name='attendance_history'),
    path('owner/income/', views.income_report, name='income_report'),
]
