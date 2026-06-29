from django.contrib import admin
from django.urls import include, path
from django.contrib.auth import views as auth_views
from academy import views as academy_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', academy_views.admin_login, name='login'),
    path('admin-login/', academy_views.admin_login, name='admin_login'),
    path('coach-login/', academy_views.coach_login, name='coach_login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('', include('academy.urls')),
]
