from django.contrib.syndication.feeds import Feed
from django.core import urlresolvers
from publicsite.models import Event, Lawmaker
import time
import datetime
from django.http import Http404, HttpResponse
import vobject
from django.db.models import Q

EVENT_ITEMS = (
    ('uid', 'uid'),
    ('dtstart', 'start'),
    ('dtend', 'end'),
    ('summary', 'summary'),
    ('location', 'location'),
)

def _date_time_to_datetime(date, time=None):
    if not time:
        time = datetime.time()
    return datetime.datetime(date.year, date.month, date.day, time.hour, time.minute, time.second)

class IcalFeed(object):

    def __call__(self, *args, **kwargs):

        cal = vobject.iCalendar()

        for item in self.items():

            event = cal.add('vevent')

            for vkey, key in EVENT_ITEMS:
                value = getattr(self, 'item_' + key)(item)
                if value:
                    event.add(vkey).value = value

        response = HttpResponse(cal.serialize())
        response['Content-Type'] = 'text/calendar'

        return response

    def item_location(self, item):
        pass

    def items(self):
        return Event.objects.ical()

    def item_uid(self, item):
        return str(item.id)

    def item_start(self, item):
        return _date_time_to_datetime(item.start_date, item.start_time)

    def item_end(self, item):
        if item.end_date:
            end_date = item.end_date
        else:
            end_date = item.start_date

        if item.end_time:
            end_time = item.end_time
        else:
            end_time = item.start_time

        return _date_time_to_datetime(end_date, end_time)

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
            #print '1'
            raise Http404
        try:
            #print 'looking for id: %s' % (bits[0])
            # ignore those with leadership accounts - not sure what's going on with this. 
            lm_list = Lawmaker.objects.filter(crp_id=bits[0]).filter(Q(affiliate__isnull=True)|Q(affiliate=''))
            if len(lm_list)>1:
                raise Exception('too many lawmakers returned')
            lm = lm_list[0]
            #print "got lm.affiliate = '%s' " % (lm.affiliate)
            return lm
        except Exception as e:
            #print '2: %s' % (e)
            raise Http404


    def title(self, obj):
        if not obj:
            #print '3'
            raise Http404
        return "PartyTime events for %s" % obj.name

    def link(self, obj):
        if not obj:
            #print '4'
            raise Http404
        return "/feeds/pol/" + obj.crp_id

    def item_link(self, item):
        if not item:
            #print '5'
            raise Http404
        return urlresolvers.reverse('partytime.publicsite.views.party', kwargs={'docid': item.id})  

    def description(self, obj):
        if not obj:
            #print '6'
            raise Http404
        return "Parties for %s from the Sunlight Foundation" % obj.name

    def items(self, obj):
        if obj==None:
            return []
        items = Event.objects.filter(status='', beneficiaries__crp_id=obj.crp_id).order_by('-start_date','-start_time')[:10]
        if not items:
            #print '7'
            raise Http404
        else:
            return items

