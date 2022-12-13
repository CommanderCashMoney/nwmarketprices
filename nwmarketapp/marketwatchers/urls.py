from django.urls import path

from . import views


urlpatterns = [
    path('', views.marketwatchers, name='marketwatchers'),
    path('buy_orders/', views.buy_orders, name='buy_orders')
]
