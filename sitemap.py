from django.contrib.sitemaps import Sitemap
from publicsite.models import *

class EventSitemap(Sitemap):
    def items(self):
        return Event.objects.all()

    def lastmod(self, obj):
        return obj.added

class CommitteeSitemap(Sitemap):
    def items(self):
        return Committee.objects.all()

class HostSitemap(Sitemap):
    def items(self):
        return Host.objects.all()

    def location(self, obj):
        return '/search/Host/%s/' % obj.name

class VenueSitemap(Sitemap):
    def items(self):
        return Venue.objects.all()

    def location(self, obj):
        return '/search/Venue_Name/%s/' % obj.venue_name

class LawmakerSitemap(Sitemap):
    def items(self):
        return Lawmaker.objects.all()

    def location(self, obj):
        return '/pol/%s' % obj.crp_id


sitemaps = {'events': EventSitemap, 
            'committees': CommitteeSitemap,
            'hosts': HostSitemap,
            'venues': VenueSitemap,
            'lawmakers': LawmakerSitemap,
           }
