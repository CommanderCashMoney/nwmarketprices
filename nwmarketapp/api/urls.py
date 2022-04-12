from django.urls import path

from . import views


urlpatterns = [
    path('version/', views.current_scanner_version, name='version'),
    path('submit_bad_names/', views.submit_bad_names, name='submit_bad_names'),
    path('confirmed_names/', views.confirmed_names, name='confirmed_names'),
    path('get_mapping_corrections/', views.get_mapping_corrections, name='get_mapping_corrections'),
    path('word-cleanup/', views.word_cleanup, name='name-cleanup'),
    path('typeahead/', views.typeahead, name='typeahead'),
]
