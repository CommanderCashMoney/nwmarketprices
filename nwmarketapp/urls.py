from django.urls import re_path
from django.urls import path
from . import views
urlpatterns = [
    path('', views.index, name='index'),
    path('<str:item_id>/<int:server_id>/', views.index, name='index'),
    path('cn/', views.confirmed_names, name='cn'),
    path('nc/', views.name_cleanup, name='nc'),
    path('typeahead/', views.typeahead, name='typeahead'),
    path('latest_prices/', views.latest_prices, name='latest_prices'),
    path('servers/', views.servers, name='servers'),
    path('api/<int:item_id>/<int:server_id>/', views.get_item_history, name='item_history'),
]
