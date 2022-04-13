from django.urls import path
from . import views
from nwmarketapp.api.views import names, deprecated, prices

urlpatterns = [
    path('', views.index, name='index'),
    path('<int:server_id>/', views.index, name='index'),
    path('<int:server_id>/<str:item_id>/', views.index, name='index'),

    # old endpoints shifted to /api/ - deprecate these urls. give a grace period to swap over.
    path('cn/', names.confirmed_names_v1, name='cn'),
    path('latestprices/', prices.latest_prices_v1),
    path('servers/', names.servers_v1),
    path('popular_items/<int:server_id>/', prices.get_popular_items_v1),
]
