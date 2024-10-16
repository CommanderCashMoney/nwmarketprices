"""nwmarket URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.urls import re_path
from django.conf.urls import include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView
)

from django.contrib.sitemaps.views import sitemap
from nwmarketapp.sitemap import ServersSitemap
from nwmarketapp.views import MyTokenObtainPairView
from nwmarketapp.views import PricesUploadAPI, NameCleanupAPI, ConfirmedNamesAPI


urlpatterns = [
    path('', include('nwmarketapp.urls')),
    path('admin/clearcache/', include('clearcache.urls')),
    path('admin/', admin.site.urls),
    path('api/token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),

    path('api/scanner_upload/', PricesUploadAPI.as_view(), name='scanner_upload'),
    path('api/name_cleanup_upload/', NameCleanupAPI.as_view(), name='name_cleanup_upload'),
    path('api/confirmed_names_upload/', ConfirmedNamesAPI.as_view(), name='confirmed_names_upload'),
    path('api/', include('nwmarketapp.api.urls')),
    path('account/', include('allauth.urls')),
    path('account/', include('nwmarketapp.profile.urls')),
    path('sitemap.xml', sitemap, {'sitemaps': {'servers': ServersSitemap}}, name='django.contrib.sitemaps.views.sitemap'),
    path('mw/', include('nwmarketapp.marketwatchers.urls')),

]
