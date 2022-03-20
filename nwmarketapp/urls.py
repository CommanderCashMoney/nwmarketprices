from django.urls import re_path
from django.urls import path
from . import views
urlpatterns = [
    path('', views.index, name='index'),
    path('cn/', views.cn, name='cn'),
    path('nc/', views.nc, name='nc'),
    path('latestprices/', views.latest_prices, name='latestprices'),
    path('servers/', views.servers, name='servers'),
    path('<int:item_id>', views.index, name='index'),
    path('<int:item_id>/<int:server_id>', views.index, name='index'),


]
