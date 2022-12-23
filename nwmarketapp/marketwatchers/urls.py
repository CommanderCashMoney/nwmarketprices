from django.urls import path

from . import views


urlpatterns = [
    path('', views.marketwatchers, name='marketwatchers'),
    path('buy_orders/', views.buy_orders, name='buy_orders'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('price_changes/', views.price_changes, name='price_changes')
]
