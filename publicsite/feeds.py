from django.contrib.syndication.feeds import Feed
from django.core import urlresolvers
from publicsite.models import Event, Lawmaker
import time 
import datetime
from publicsite.management.icalendarfeed import ICalendarFeed

class IcalFeed(ICalendarFeed):

    def items(self):
        return Event.objects.ical()

    def item_uid(self, item):
        return str(item.id)

    def item_start(self, item):
        if item.start_time:
            start_time = item.start_time
        else:
            start_time= "00:00:00"	
        return datetime.datetime(*time.strptime(str(item.start_date) +" "+ str(start_time),"%Y-%m-%d %H:%M:%S")[0:5])

    def item_end(self, item):
        if item.end_date:
            end_date = item.end_date
        else:
	        #if there is no end date defined, the end date is the start date
            end_date= item.start_date

        if item.end_time:
            end_time = item.end_time
        else:
            end_time= "23:59:00"
        return datetime.datetime(*time.strptime(str(end_date) +" "+ str(end_time),"%Y-%m-%d %H:%M:%S")[0:5])

    def item_summary (self, item):
        summaryStr=""
        if item.entertainment:
            summaryStr = summaryStr+unicode(str(item.entertainment), errors='ignore')
        try:        
            if item.venue:
                summaryStr = summaryStr+" @ "+unicode(str(item.venue), errors='ignore')
        except:
            pass
        if item.beneficiaries:
            summaryStr = summaryStr+" For: "
            for beneficiary in item.beneficiaries.all():
                summaryStr = summaryStr+unicode(str(beneficiary), errors='ignore')
	    #print(item.id)	
	    #print(summaryStr)
        summaryStr = summaryStr.replace('&','')
        return summaryStr

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


class PolFeed(Feed):
    description_template = "feeds/party_description.html"

    def get_object(self, bits):
        # In case of "/rss/beats/0613/foo/bar/baz/", or other such clutter,
        # check that bits has only one member.
        if len(bits) != 1:
            raise ObjectDoesNotExist
        return Lawmaker.objects.get(crp_id=bits[0], affiliate=None)

    def title(self, obj):
        return "PartyTime events for %s" % obj.name

    def link(self, obj):
        if not obj:
            raise FeedDoesNotExist
        return "/feeds/pol/" + obj.crp_id

    def item_link(self, item):
        return urlresolvers.reverse('partytime.publicsite.views.party', kwargs={'docid': item.id})  

    def description(self, obj):
        return "Parties for %s from the Sunlight Foundation" % obj.name

    def items(self, obj):
        return Event.objects.filter(status='', beneficiaries__crp_id=obj.crp_id).order_by('-start_date','-start_time')[:10]

