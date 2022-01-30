from django.urls import re_path
from django.urls import path
from . import views
urlpatterns = [
    path('', views.index, name='index'),
    path('cn/', views.cn, name='cn'),
    path('<int:item_id>/', views.index, name='index')

]
