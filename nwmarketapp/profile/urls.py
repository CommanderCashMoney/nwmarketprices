from django.urls import path

from . import views


urlpatterns = [
    path('profile/', views.profile, name='profile'),
    path('profile/password-set/', views.set_password, name='set-password'),
]
