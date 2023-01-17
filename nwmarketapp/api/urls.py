from django.urls import path

from .views import names, prices, scanner


urlpatterns = [
    path('version/', scanner.current_scanner_version, name='version'),

    path('submit_bad_names/', names.submit_bad_names, name='submit_bad_names'),
    path('confirmed_names/', names.confirmed_names, name='confirmed_names'),
    path('get_mapping_corrections/', names.get_mapping_corrections, name='get_mapping_corrections'),
    path('word-cleanup/', names.word_cleanup, name='name-cleanup'),

    path('typeahead/', names.typeahead, name='typeahead'),

    path('latest-prices/<int:server_id>/', prices.latest_prices, name='latest-prices'),
    path('price-data/<int:server_id>/<str:item_id>/', prices.get_item_data, name='item-data'),
    path('server-price-data/<int:server_id>/', prices.initial_page_load_data, name="initial-page-load-data"),
    path('servers/', names.servers, name="servers"),
    path('servers_updated/', prices.server_scan_times, name='server_scan_times'),

    # path('update-server-prices/<int:server_id>/', prices.update_server_prices, name="update-server-prices"),
]
