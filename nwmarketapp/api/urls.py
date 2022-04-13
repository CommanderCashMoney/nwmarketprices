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
    path('server-price-data/<int:server_id>/', prices.intial_page_load_data, name="intial-page-load-data"),
    path('servers/', names.servers, name="servers"),

    # to deprecate
    path('price-data-v1/<int:server_id>/<str:item_id>/', prices.get_item_data_v1, name="price-data"),
    path('popular-items-v1/<int:server_id>/', prices.get_popular_items_v1, name='index'),
    path('servers-v1/', names.servers, name='servers-v1'),  # not real json
]
