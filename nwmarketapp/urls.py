from django.urls import path
from . import views
urlpatterns = [
    path('', views.index, name='index'),
    path('cn/', views.confirmed_names_v1, name='cn'),
    path('nc/', views.name_cleanup_v1, name='nc'),
    path('latestprices/', views.latest_prices, name='latestprices'),
    path('servers/', views.servers, name='servers'),
    path('<int:item_id>', views.index, name='index'),
    path('<int:item_id>/<int:server_id>', views.index, name='index'),
    path('popular_items/<int:server_id>', views.get_popular_items, name='index'),
    path('popular_items_old/<int:server_id>', views.get_popular_items_old, name='index'),
    path('price-data/<int:server_id>/<int:item_id>/', views.price_data, name="price-data"),
    path('server-price-data/<int:server_id>/', views.intial_page_load_data, name="intial-page-load-data"),
]
