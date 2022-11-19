from django.contrib.sitemaps import Sitemap
from .models import Servers



class ServersSitemap(Sitemap):
    protocol = 'https'
    changefreq = 'daily'

    def items(self):
        return Servers.objects.all()

    def lastmod(self, obj):
        return obj.last_updated
class NewsSitemap(Sitemap):
    protocol = 'https'
    changefreq = 'daily'

    def items(self):
        return Servers.objects.all()

    def lastmod(self, obj):
        return obj.last_updated


