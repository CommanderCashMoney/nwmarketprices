from django.urls import path

from . import views


urlpatterns = [
    path('version/', views.current_scanner_version, name='index'),
]
