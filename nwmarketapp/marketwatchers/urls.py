from django.urls import path
from .views import dashboard, order_tracking

urlpatterns = [
    path('', order_tracking.marketwatchers, name='marketwatchers'),
    path('buy_orders/', order_tracking.buy_orders, name='buy_orders'),
    path('dashboard/<int:server_id>/', dashboard.dashboard, name='dashboard'),
    path('price_changes/<int:server_id>/', dashboard.price_changes, name='price_changes'),
    path('rare_items/<int:server_id>/', dashboard.rare_items, name='rare_items'),
    path('dashboard_items/<int:server_id>/', dashboard.get_dashboard_items, name='dashboard_items'),
    path('tracked_items_save/', dashboard.tracked_items_save, name='tracked_items_save'),
]
