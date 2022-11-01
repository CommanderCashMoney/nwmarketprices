from django.urls import path
from . import views
from nwmarketapp.api.views import names, deprecated, prices

urlpatterns = [
    path('', views.index, name='index'),
    path('<int:server_id>/', views.index, name='index'),
    path('<str:item_id>/<int:server_id>/', views.index, name='index'),
    path('ads.txt', views.ads, name='ads'),

]
