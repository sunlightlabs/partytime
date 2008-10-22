from django.contrib.syndication.feeds import Feed
from django.core import urlresolvers
from publicsite.models import Event

class RecentFeed(Feed):
    title = "Party Time Recent Parties"
    link = "/feeds/recent/"
    description = "Recent parties"
    title_template = "feeds/party_title.html"
    description_template = "feeds/party_description.html"
    
    def items(self):
        return Event.objects.recent()
        
    def item_link(self, item):
        return urlresolvers.reverse('partytime.publicsite.views.party', kwargs={'docid': item.id})

class UpcomingFeed(Feed):
    title = "Party Time Upcoming Parties"
    link = "/feeds/upcoming/"
    description = "Upcoming parties"
    
    title_template = "feeds/party_title.html"
    description_template = "feeds/party_description.html"
    
    def items(self):
        return Event.objects.upcoming()

    def item_link(self, item):
        return urlresolvers.reverse('partytime.publicsite.views.party', kwargs={'docid': item.id})  