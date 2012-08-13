import mimetypes
import math
import random
try:
    import json
except ImportError:
    import simplejson
import time
import datetime
import random

from django import forms
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core import serializers
from django.core.mail import send_mail, EmailMultiAlternatives
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.db.models import Q
from django.db.models.query import QuerySet
from django.db.utils import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.http import HttpResponseServerError, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils.encoding import smart_str
from django.views.decorators.cache import cache_page


from partytime.publicsite.models import *
from wordpress.models import Post
from layar import LayarView, POI

# catch-all cache time
# set low during development
cache_time_minutes = 1

@cache_page(60*cache_time_minutes)
def index(request):


    blog_posts = Post.objects.published().select_related()[:2]    
    upcoming_events = Event.objects.upcoming(2)
    newest_events = Event.objects.newest(2)
    
    # cache the partiesheldforleadership template tags etc for this long in seconds. Some of them are ridiculous to generate. 
    # Caching them all for different times decreases the likelihood they'll all need to get regened at the same page load. 
    cachetime1 = 10
    cachetime2 = 10
    cachetime3 = 10
    cachetime4 = 10
    
    
    return render_to_response(
            'publicsite_redesign/indextest.html', 
            {'post_list': blog_posts,
            'upcoming_events':upcoming_events,
            'newest_events':newest_events, 
            'cachetime1':cachetime1,
            'cachetime2':cachetime2,
            'cachetime3':cachetime3,
            'cachetime4':cachetime4,                        
            })

def make_paginator_text(base_html, current_page, max_page):
    
    if max_page==1:
        return ""
    
    initial_page = current_page - 3
    
    if current_page < 5:
        initial_page = 1
    
    if current_page > max_page-2:
        initial_page = max_page - 5

    
    return_html = ""
    if current_page > 1:
        return_html += '<span class="prev"><a class="textReplace" href="' + base_html + '?page=' + str(current_page-1) + '">Previous</a></span>'
        
    end_page = initial_page+6
    if end_page > max_page:
        end_page = max_page+1
    
    if initial_page < 1:
        initial_page = 1
    
    for i in range(initial_page, end_page):
        
    
        return_html += '<span class="pageNum ' 
        if i==current_page:
            return_html += 'cur">'  + str(i) + '</span>'
        else:
            return_html += '"><a href="' + base_html + '?page=' + str(i) + '">' + str(i) + '</a></span>'
    
    
    if current_page < max_page:
        return_html += '<span class="next"><a class="textReplace" href="' + base_html + '?page=' + str(current_page+1) + '">Next</a></span>'
        
    return return_html


def blogindex(request):
    # need to add pagination etc. 
    blog_posts = Post.objects.published()

    paginator = Paginator(blog_posts, 5)
    pagenum = request.GET.get('page', 1)
    max_page = paginator.num_pages, 
    
    try:
        page = paginator.page(pagenum)
    except (EmptyPage, InvalidPage):
        raise Http404
    
    paginator_html = make_paginator_text('/blogindex/', int(pagenum), max_page[0])
    
    return render_to_response(
            'publicsite_redesign/blogindex.html', 
            {'post_list': page.object_list,
            'paginator_html':paginator_html,
            }
            )

def party(request, docid): 
    doc = get_object_or_404(Event, pk=docid)
    return render_to_response('publicsite_redesign/party.html', {"doc": doc}) 


@cache_page(60*cache_time_minutes)
def recent(request):
    events = Event.objects.recent(60)
    print "recent"
    paginator = Paginator(events, 10)
    pagenum = request.GET.get('page', 1)
    max_page = paginator.num_pages
    
    try:
        page = paginator.page(pagenum)
    except (EmptyPage, InvalidPage):
        raise Http404
        

    paginator_html = make_paginator_text('/recent/', int(pagenum), max_page)
    rss_url = "/feeds/recent/"
     
    return render_to_response(
            'publicsite_redesign/generic_results.html', 
            {'title': 'Recent events', 
             'results': page.object_list,
             'paginator_html':paginator_html,
             'rss_url':rss_url,
             'widget_url':'/widget/recent/',
             }
            )
            
@cache_page(60*cache_time_minutes)
def upcoming(request):
    events = Event.objects.upcoming(None)
    paginator = Paginator(events, 10)
    pagenum = request.GET.get('page', 1)
    max_page = paginator.num_pages
    paginator_html = ""
    # There typically aren't enough results for there to be multiple pages

    rss_url = "/feeds/upcoming/"
        
    try:
        page = paginator.page(pagenum)
    except (EmptyPage, InvalidPage):
        raise Http404

    return render_to_response(
            'publicsite_redesign/generic_results.html', 
            {'title': 'Upcoming events', 
             'results': page.object_list,
             'paginator_html':paginator_html,
             'rss_url':rss_url,
             'widget_url':'/widget/upcoming/',
             }
            )

@cache_page(60*cache_time_minutes)
def newly_added(request):
    events = Event.objects.newest(10).select_related('beneficiaries', 'venue')
    paginator = Paginator(events, 10)
    pagenum = request.GET.get('page', 1)
    max_page = paginator.num_pages
    paginator_html = ""
    # There typically aren't enough results for there to be multiple pages

    rss_url = "/feeds/newlyadded/"

    try:
        page = paginator.page(pagenum)
    except (EmptyPage, InvalidPage):
        raise Http404

    return render_to_response(
            'publicsite_redesign/generic_results.html', 
            {'title': 'Newly added events', 
             'results': page.object_list,
             'paginator_html':paginator_html,
             'rss_url':rss_url,
             'widget_url':'/widget/newly-added/',
             }
            )

@cache_page(60*cache_time_minutes)
def committee_leadership(request):

    today = datetime.date.today()
    pagenum = request.GET.get('page', 1)
    crp_ids = list(CommitteeMembership.objects.values_list('member__crp_id', flat=True).exclude(position='Member'))
    leadership_ids = list(Lawmaker.objects.filter(crp_id__in=crp_ids).values_list('id', flat=True))

    events = Event.objects.filter(status="", beneficiaries__in=leadership_ids, start_date__lte=today).select_related('beneficiaries', 'venue').distinct().order_by('-start_date', 'start_time')[:60]

    paginator = Paginator(events, 10)
    pagenum = request.GET.get('page', 1)
    
    max_page = paginator.num_pages
    paginator_html = ""
    # There typically aren't enough results for there to be multiple pages
    paginator_html = make_paginator_text('/committee-leadership/', int(pagenum), max_page)    

    try:
        page = paginator.page(pagenum)
    except (EmptyPage, InvalidPage):
        raise Http404

    return render_to_response(
            'publicsite_redesign/generic_results.html', 
            {'title': 'Recent Events held for committee leaders', 
             'results': page.object_list,
             'paginator_html':paginator_html,
             'current_pagenum':pagenum,
             'max_pagenum':'6'}
            )
            
@cache_page(60*cache_time_minutes)
def congressional_leadership(request):

    today = datetime.date.today()
    pagenum = request.GET.get('page', 1)
    leader_ids = LeadershipPosition.objects.values_list('lawmaker_id', flat=True)
    events = Event.objects.filter(status="", beneficiaries__pk__in=leader_ids, start_date__lte=today).distinct().select_related('beneficiaries', 'venue').order_by('-start_date', 'start_time')[:60]

    paginator = Paginator(events, 10)
    pagenum = request.GET.get('page', 1)
    
    max_page = paginator.num_pages
    paginator_html = ""
    # There typically aren't enough results for there to be multiple pages
    paginator_html = make_paginator_text('/congressional-leadership/', int(pagenum), max_page)    

    try:
        page = paginator.page(pagenum)
    except (EmptyPage, InvalidPage):
        raise Http404

    return render_to_response(
            'publicsite_redesign/generic_results.html', 
            {'title': 'Recent Parties Held for Congressional Leadership', 
             'results': page.object_list,
             'paginator_html':paginator_html,
             'current_pagenum':pagenum,
             'max_pagenum':'6'}
            )      


@cache_page(60*cache_time_minutes)
def hosted_by_congressional_leadership(request):

    today = datetime.date.today()
    pagenum = request.GET.get('page', 1)
    leader_ids = LeadershipPosition.objects.values_list('lawmaker__crp_id', flat=True)
    events = Event.objects.filter(status="", other_members__crp_id__in=leader_ids, start_date__lte=today).distinct().select_related('beneficiaries', 'venue').order_by('-start_date', 'start_time')[:60]

    paginator = Paginator(events, 10)

    max_page = paginator.num_pages
    paginator_html = ""
    # There typically aren't enough results for there to be multiple pages
    paginator_html = make_paginator_text('/hosted-by-congressional-leadership/', int(pagenum), max_page)    

    try:
        page = paginator.page(pagenum)
    except (EmptyPage, InvalidPage):
        raise Http404

    return render_to_response(
            'publicsite_redesign/generic_results.html', 
            {'title': 'Recent Parties Hosted by Congressional Leadership', 
             'results': page.object_list,
             'paginator_html':paginator_html,
             'current_pagenum':pagenum,
             'max_pagenum':'6'}
            )      


@cache_page(60*cache_time_minutes)
def presidential(request):

    today = datetime.date.today()
    pagenum = request.GET.get('page', 1)
    events = Event.objects.filter(status="", is_presidential=True, start_date__lte=today).distinct().select_related('beneficiaries', 'venue').order_by('-start_date', 'start_time')[:60]

    paginator = Paginator(events, 10)
    pagenum = request.GET.get('page', 1)

    max_page = paginator.num_pages
    paginator_html = ""
    # There typically aren't enough results for there to be multiple pages
    paginator_html = make_paginator_text('/presidential/', int(pagenum), max_page)    

    try:
        page = paginator.page(pagenum)
    except (EmptyPage, InvalidPage):
        raise Http404
    
    rss_url = '/feeds/presidential/'
    
    return render_to_response(
            'publicsite_redesign/generic_results.html', 
            {'title': 'Recent Parties Hosted For Presidential Candidates', 
             'results': page.object_list,
             'paginator_html':paginator_html,
             'rss_url':rss_url,
             'current_pagenum':pagenum,
             'max_pagenum':'6',
             'widget_url':'/widget/presidential/'}
            )


def search_proxy(request):
    field = request.REQUEST.get('field', None)
    args = request.REQUEST.get('args', None)

    if field and args:
        redirect_url = '/search/%s/%s/' % (field, args)
        return HttpResponseRedirect(redirect_url)

    return HttpResponseRedirect('/')

field_name_fix={
    'beneficiary':'beneficiary',
    'host':'host',
    'other_members_of_congress':'other member of congress',
    'venue_name':'venue',
    'entertainment_type':'entertainment type',
    'tags':'tags'
    }

def search(request, field, args):
    lawmakers = None

    if field == 'Beneficiary':
        lawmakers = Lawmaker.objects.filter(name__icontains=args)
        if len(lawmakers)==1:
            if lawmakers[0].crp_id and not lawmakers[0].affiliate:
                return HttpResponseRedirect('/pol/'+lawmakers[0].crp_id)               

    if lawmakers is not None:
        lawmakers = lawmakers.filter(affiliate=None).exclude(crp_id=None)
    
    fixed_field = field.lower()
    events = Event.objects.by_field(fixed_field, args)
    formatted_field = field_name_fix[fixed_field]
    title = "Search results for '%s' in %s" % (args, formatted_field)
    
    paginator = Paginator(events, 10)
    pagenum = request.GET.get('page', 1)

    max_page = paginator.num_pages
    paginator_html = ""
    # There typically aren't enough results for there to be multiple pages
    search_url_base = "/search/%s/%s/" % (field, args)
    paginator_html = make_paginator_text(search_url_base, int(pagenum), max_page)    
    print "paginator: " + paginator_html
    
    try:
        page = paginator.page(pagenum)
    except (EmptyPage, InvalidPage):
        raise Http404
    
    
    return render_to_response(
            'publicsite_redesign/generic_results.html',
            {'title':title,
            'field':field,
             'results': page.object_list,
             'lawmakers': lawmakers, 
             'paginator_html':paginator_html, 
             'current_pagenum':pagenum,
             'max_pagenum':max_page,
             }
            )
            
            

def polwithpac(request, cid):
    lawmaker = None
    pacname = None

    possible_lawmakers = Lawmaker.objects.filter(crp_id=cid).distinct()

    if possible_lawmakers.count() == 0:
        return HttpResponseRedirect('/')     

    for this_lawmaker in possible_lawmakers:
        if this_lawmaker.affiliate:
            pacname = this_lawmaker.name
        else:
            lawmaker = this_lawmaker

    events = Event.objects.filter(status='', beneficiaries__crp_id=cid).order_by('-start_date', '-start_time').distinct()
    
    # need to get pictures of 'em
    image_url = None
    
    event_count = events.count()
    paginator = Paginator(events, 10)
    pagenum = request.GET.get('page', 1)

    max_page = paginator.num_pages
    paginator_html = ""
    # There typically aren't enough results for there to be multiple pages
    search_url_base = "/pol/%s/" % (cid)
    paginator_html = make_paginator_text(search_url_base, int(pagenum), max_page)    
    print "paginator: " + paginator_html
    
    try:
        page = paginator.page(pagenum)
    except (EmptyPage, InvalidPage):
        raise Http404
    
    return render_to_response(
            'publicsite_redesign/entity_politician.html',
            {'results': page.object_list,
             'lawmaker': lawmaker,
             'pacname': pacname,
             'image_url': image_url, 
             'event_count':event_count,
             'paginator_html':paginator_html, 
             'current_pagenum':pagenum,
             'max_pagenum':max_page,             
             }
            )
# new search that looks in multiple places for matches and then does... something.... 

def multisearch(request):
    query = request.GET.get('q')
    error_message = None
    lawmakers = None
    venues = None
    entertainments = None
    hosts = None
    
    if not (query):
        raise Http404
    
    if len(query)>3:
    
        lawmakers = Lawmaker.objects.filter(Q(name__icontains=query)|Q(affiliate__icontains=query)).distinct()
    
        hosts = Host.objects.filter(name__icontains=query).values('name').distinct()
    
        venues = Venue.objects.filter(venue_name__icontains=query).values('venue_name').distinct()
    
        entertainments = Event.objects.filter(entertainment__icontains=query).values('entertainment').distinct()
        
        cities = Venue.objects.filter(city__icontains=query).values('city', 'state').distinct()
    else:
        error_message = "Search term must be at least three letters long"
    
    if ( (len(lawmakers) + len(hosts) + len(venues) + len(entertainments) + len(cities)) == 0 ):
        error_message = "No matches"
    
    return render_to_response(
    'publicsite_redesign/multisearch.html', 
    {'query':query,
    'lawmakers':lawmakers,
    'venues':venues,
    'entertainments':entertainments,
    'hosts':hosts, 
    'cities':cities,
    'error_message':error_message,
    })

def calendar_today(request):
    today = datetime.date.today()
    dayofweek = today.weekday()
    
    week_start = today - datetime.timedelta(days=dayofweek)
    
    response = calendar(request, week_start.strftime("%Y%m%d"))
    return response
    
def calendar(request, datestring):
    # looking for queryarg: q=YYYYMMDD
    startdate = None
    try:
        startdate = datetime.date(int(datestring[0:4]), int(datestring[4:6]), int(datestring[6:8]))
    except ValueError:
        raise Http404
    
    dayofweek = startdate.weekday()
    
    
    week_start = startdate - datetime.timedelta(days=dayofweek)
    
    # redirect if the start date isn't a sunday. 
    
    if (dayofweek != 0):
        newurl = "/calendar/%s/" % (week_start.strftime("%Y%m%d"))
        return HttpResponseRedirect(newurl) 
    
    week_end = week_start + datetime.timedelta(days=6)
    
    this_day = week_start
    week_data = []
    
    nextweekstart = week_start + datetime.timedelta(days=7)
    lastweekstart = week_start - datetime.timedelta(days=7)
    
    next_week_url = "/calendar/%s/" % (nextweekstart.strftime("%Y%m%d"))
    last_week_url = "/calendar/%s/" % (lastweekstart.strftime("%Y%m%d"))
    
    for day in ('SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'):
        events = Event.objects.filter(start_date=this_day, status='').order_by('start_time')
        todays_data = {
        'dayname':day,
        'date':this_day,
        'events':events,
        }
        week_data.append(todays_data)
        this_day = this_day + datetime.timedelta(days=1)
    
    
    
    return render_to_response(
    'publicsite_redesign/calendar.html', 
    {
    'week_data':week_data,
    'week_start':week_start,
    'week_end':week_end,
    'next_week_url':next_week_url,
    'last_week_url':last_week_url,
    'datestring':datestring,
    'cache_key':'calendar-' + datestring,
    'cache_time':10,
    }
    )
           


def widget_upcoming(request):
    events = Event.objects.upcoming(5)
    widget_title = "Upcoming events"
    return render_to_response(
    'publicsite_redesign/widget.html', 
    {
    'events':events,
    'widget_title':widget_title,
    })

def widget_recent(request):
    events = Event.objects.recent(5)
    widget_title = "Recent events"
    return render_to_response(
    'publicsite_redesign/widget.html', 
    {
    'events':events,
    'widget_title':widget_title,
    })

def widget_newly_added(request):
    events = Event.objects.newest(5)
    widget_title = "Newly added events"
    return render_to_response(
    'publicsite_redesign/widget.html', 
    {
    'events':events,
    'widget_title':widget_title,
    })

def widget_presidential(request):
    today = datetime.date.today()
    events = Event.objects.filter(status="", is_presidential=True, start_date__lte=today).distinct().select_related('beneficiaries', 'venue').order_by('-start_date', 'start_time')[:5]
    widget_title = "Recent presidential events"
    return render_to_response(
    'publicsite_redesign/widget.html', 
    {
    'events':events,
    'widget_title':widget_title,
    })        

def widget_pol(request, crp_id):
    possible_lawmakers = Lawmaker.objects.filter(crp_id=crp_id).distinct()

    lawmaker = None
    
    if possible_lawmakers.count() == 0:
        return Http404     

    for this_lawmaker in possible_lawmakers:
        if this_lawmaker.affiliate:
            pacname = this_lawmaker.name
        else:
            lawmaker = this_lawmaker

    events = Event.objects.filter(status='', beneficiaries__crp_id=crp_id).order_by('-start_date', '-start_time').distinct()[:5]
    
    lawmaker_name = lawmaker.titled_name()
    widget_title = "Events for %s" % (lawmaker_name)
    
    return render_to_response(
    'publicsite_redesign/widget.html', 
    {
    'events':events,
    'widget_title':widget_title,
    })

def search_old(request, field, args):
    lm = None

    if field == 'Beneficiary':
        lm = Lawmaker.objects.filter(name__icontains=args)
        if len(lm)==1:
            if lm[0].crp_id and not lm[0].affiliate:
                return HttpResponseRedirect('/pol/'+lm[0].crp_id)               

    if lm is not None:
        lm = lm.filter(affiliate=None).exclude(crp_id=None)

    events = Event.objects.by_field(field.lower(), args)

    return render_to_response(
            'publicsite/search_results.html',
            {'field': field,
             'args': args,
             'docset': events,
             'lm': lm, },
            context_instance = RequestContext(request)
            )


def search_embed(request, field, args):
    events = Event.objects.by_field(field.lower(), args)
    return render_to_response(
            'publicsite/search_embed.html',
            {'field': field, 
             'args':args, 
             'docset':events, }, 
            context_instance = RequestContext(request)
            )


def search_embed_flex(request, field, args):
    events = Event.objects.by_field(field.lower(), args).order_by('start_date')[:3]
    return render_to_response(
            'publicsite/search_embed_flex.html', 
            {'field': field, 'args': args, 'docset': events, }, 
            context_instance = RequestContext(request)
            )


def convention_list(request, convention=''):
    conventions = {
        'republican': 'GOP convention',
        'democratic': 'Democratic convention',
    }

    args = conventions.get(convention, 'convention')
    
    events = Event.objects.filter(status='', tags__tag_name__icontains=args) \
                          .exclude(start_date__isnull=True) \
                          .order_by('start_date', 'start_time')
    
    return render_to_response(
            'publicsite/search_results.html', 
            {'field': 'Tags',
             'args': args, 
             'docset': events, }
            )







def upcoming_embed(request):
    docset = Event.objects.upcoming(5)
    return render_to_response(
            'publicsite/upcoming_embed.html',
            {'snapshot_image_name': 'upcoming',
                'docset': docset, }
            )


def upcoming_embed2(request):
    docset = Event.objects.upcoming(5)
    return render_to_response(
            'publicsite/upcoming_embed_2.html', 
            {'snapshot_image_name': 'upcoming', 
             'docset':docset, }
            )


def bydate(request,start,end):
    docset = Event.objects.daterange(start, end)
    paginator = Paginator(docset, 25, orphans=5)
    pagenum = request.GET.get('page', 1)
    try:
        page = paginator.page(pagenum)
    except (EmptyPage, InvalidPage):
        raise Http404

    return render_to_response(
                'publicsite/snapshot.html', 
                {'snapshot_image_name': '', 
                 'page': page, }
                )


#
# widgets
#

def abc_convention(request, convention=''):
    conventions = {
        'republican': 'gop convention',
        'democratic': 'democratic convention',
    }
    
    arg = conventions.get(convention, None)
    
    if arg:
        events = Event.objects.filter(
                status='',
                tags__tag_name=arg)
        event_count = events.count()
        
        if event_count > 0:
            randdocnum = random.randint(0, event_count - 1)
            event = events[randdocnum]
            
            return render_to_response(
                    'publicsite/widgets/abc_convention.html',
                    {'field': 'Tags', 
                     'args': arg, 
                     'doc': event, 
                     'convention': convention, }
                    )


def widget180_upcoming(request):
    events = Event.objects.filter(start_date__gte=datetime.datetime.now(), status='') \
                          .exclude(entertainment="") \
                          .order_by('start_date', 'start_time')[:3]

    return render_to_response(
            'publicsite/widgets/widget_180.html',
            {'docset': events, }
            )


def jsonCID(request, CID):
    from django.core import serializers

    events = Event.objects.filter(beneficiaries__crp_id=CID, status='') \
                          .order_by('start_date', 'start_time')

    try:
        data = serializers.serialize('json', 
                                     events, 
                                     fields=('committee_id',
                                             'start_date',
                                             'start_time',
                                             'entertainment',
                                             'venue',
                                             'contributions_info',
                                             'hosts',
                                             'beneficiaries',
                                             'make_checks_payable_to'), 
                                     use_natural_keys=True)
    except:
        data = ''    

    return HttpResponse(data)


def widget_state(request, state):
    q = Q()
    cids = Lawmaker.objects.filter(crp_id__isnull=False, state=state) \
                           .values('crp_id') \
                           .distinct()

    for cid in cids:
        q = q | Q(beneficiaries__crp_id=cid['crp_id'])

    docset = Event.objects.filter(status='', start_date__gte=datetime.datetime.now()) \
                          .filter(q) \
                          .order_by('start_date', 'start_time')[:6]

    return render_to_response(
            'publicsite/widgets/state.html',
            {'docset':docset, 
             'state': state, }
            )


def leadpac_all(request):
    docset = Event.objects.filter(status='', beneficiaries__affiliate__isnull=False) \
			  .exclude(beneficiaries__affiliate='') \
                          .order_by('-start_date', '-start_time')
    paginator = Paginator(docset, 25, orphans=5)
    pagenum = request.GET.get('page', 1)
    try:
        page = paginator.page(pagenum)
    except (EmptyPage, InvalidPage):
        raise Http404

    return render_to_response(
            'publicsite/snapshot.html', 
            {'snapshot_image_name': '', 'page': page, }
            )


def leadpacs(request):
    docset = Event.objects.filter(status='', beneficiaries__affiliate__isnull=False) \
                          .order_by('-start_date', '-start_time')[0:6]

    return render_to_response(
            'publicsite/leadpacs.html', 
            {'docset': docset, })




#
# file uploading
#

def upload(request):
    if request.method == 'POST' and request.FILES:
        uf = request.FILES.get('pdf', None)

        if uf:
            timestamp = str(time.time()).split('.')[0]

            fname = uf.name.replace(' ', '_')

            local_path = '%s/%s' % (settings.FILE_UPLOAD_PATH, '%s-%s' % (timestamp, fname))
            remote_path = 'uploads/%s' % '%s-%s' % (timestamp, fname)

            from mediasync.backends.s3 import *

            with open(local_path, 'wb') as destination:
                for chunk in uf.chunks():
                    destination.write(chunk)

            mimetype, encoding = mimetypes.guess_type(local_path)

            client = Client()
            client.open()
            result = client.put(open(local_path).read(), mimetype or '', remote_path)
            client.close()

            if result:
                send_mail('[partytime] Invitation submission', 
                         'A new invitation has been submitted to Political Party Time. You may download it from http://assets.sunlightfoundation.com.s3.amazonaws.com/partytime/3.0/%s' % remote_path, 
                          'partytime@sunlightfoundation.com', 
                          ['partytime@sunlightfoundation.com', 'abycoffe+partytime@sunlightfoundation.com', ]
                          )

            return HttpResponseRedirect('/upload/thanks/')

    return render_to_response(
            'publicsite_redesign/upload.html', 
            context_instance = RequestContext(request)
            )

def upload_thanks(request):
    return HttpResponse("Thank you for your submission.")


#
# committees
#
def cmtes(request, chamber='House'):
    return render_to_response(
            'publicsite/cmte.html', 
            {'res': Committee.objects.filter(chamber=chamber), 
             'chamber': chamber, }
            )


def cmtedetail(request, cmteid):
    res = Event.objects.by_cmte(cmteid)
    paginator = Paginator(res['events'], 50, orphans=5)

    pagenum = request.GET.get('page', 1)
    try:
        page = paginator.page(pagenum)
    except (EmptyPage, InvalidPage):
        raise Http404

    return render_to_response(
            'publicsite/cmtedetail.html', 
            {'cmte': res['cmte'],
             'page': page,
             'members': res['members'],
             'since_year': res['since_year'],
             'snapshot_image_name': '',
             }
            )

def supercommittee(request):
    members = SuperCommitteeMember.objects.all()
    member_ids = members.values_list('lawmaker_id', flat=True)
    events = Event.objects.filter(
            Q(beneficiaries__id__in=member_ids) | Q(other_members__id__in=member_ids)
            ).distinct().order_by('-start_date', '-start_time')
    #events = Event.objects.filter(beneficiaries__id__in=members.values_list('lawmaker_id', flat=True)).order_by('-start_date', '-start_time').distinct()
    paginator = Paginator(events, 50, orphans=5)
    pagenum = request.GET.get('page', 1)
    try:
        page = paginator.page(pagenum)
    except (EmptyPage, InvalidPage):
        raise Http404

    return render_to_response(
            'publicsite/supercommittee.html', 
            {'page': page,
             'members': members,
             }
            )





# Marked as temporary in urls.py; not sure if this is still being used.
def updatecmtes(request,chamber):
    from sunlightapi import sunlight, SunlightApiError
    sunlight.apikey = '***REMOVED***'
    newnames=''
    Cmtes = sunlight.committees.getList(chamber)   
    for cn in Cmtes:
        c = sunlight.committees.get(cn.id)
        partyC = Committee(chamber=c.chamber, title=c.name, short=c.id)
        partyC.save()
        for om in c.members:
            try:
                l = Lawmaker.objects.get(crp_id=om.crp_id)
            except:
                l = Lawmaker(crp_id=om.crp_id, party=om.party, state=om.state, title=om.title, name=om.title+" "+om.firstname+" "+om.lastname)
                if l.title=='Rep.':
                    l.district = om.district
                l.save()
                newnames+=" "+l.name
            partyC.members.add(l)
    return HttpResponse('updated '+chamber+" added"+newnames)



def admin_uploadzip(request):    
    import os, zipfile, cStringIO
    from django.contrib.auth.decorators import login_required
    import datetime
    import shutil
    from watermark import WatermarkAdder

    watermarker = WatermarkAdder('/projects/partytime/FILES/pdfs/partytimesource.pdf')

    login_required(admin_uploadzip)

    def getzip(filename, ignoreable=100): 
        try: 
            return zipfile.ZipFile(filename) 
        except zipfile.BadZipfile: 
            original = filename.read()
            position = original.rindex(zipfile.stringEndArchive, 
                                   -(22 + ignoreable), -20) 
            coredata = cStringIO.StringIO(original[: 22 + position]) 
            return zipfile.ZipFile(coredata) 

    if request.FILES:
        f = request.FILES['file']
        zfile = getzip(f)
        for zfname in zfile.namelist():
            if zfname.startswith('.') or zfname.startswith('__'):
                continue
            if zfname[-4:]=='.pdf':
                newe = Event(status='temp', scribd_id=0)
                newe.save()
                pk = newe.pk
                localfilename = 'flyer_'+str(pk)+'_original.pdf'
                watermarked_pdf_filename = 'flyer_%s.pdf' % str(pk)
                syspath = '/projects/partytime/FILES/pdfs/'
                m = datetime.date.today().month
                if m<10:
                    strm = '0'+str(m)
                else:
                    strm = str(m)
                dirpath = str(datetime.date.today().year)+'/'+strm+'/'
                if not os.path.isdir(syspath + dirpath):
                    os.makedirs(syspath + dirpath,0777)
                destination = open(syspath + dirpath + localfilename, 'wb')
                destination.write(zfile.read(zfname))
                destination.close()
                newe.pdf_document_link = '/' + dirpath + watermarked_pdf_filename
                newe.save()

                filepath = syspath + dirpath + localfilename
                watermarked_filepath = syspath + dirpath + watermarked_pdf_filename
                try:
                    watermarker(filepath, watermarked_filepath)
                except: # Just in case the watermarking doesn't work.
                    shutil.copyfile(filepath, watermarked_filepath)

        return HttpResponseRedirect('/admin/publicsite/event/')
    else:
        return HttpResponseRedirect('/')



from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def admin_checkfordupes(request):
    from django.db.models import Q

    date = request.POST['d']
    venue = request.POST['v']
    this_event = request.POST['e']
    ben = request.POST['ben_ids'].split()

    e = Event.objects.filter(status='', venue__id=venue, start_date=date).exclude(pk=this_event) 
    q = Q()
    for b in ben:
        q = q | Q( beneficiaries=b)
    e = e.filter(q)
    s='<a a href="javascript:checkdupes()">CHECK FOR DUPES</a> <b>Is this a duplicate of:</b> '
    #s = 'venue='+str(venue)+'date='+date+'this='+str(this_event)+' ben='+request.POST['ben_ids']
    for ee in e:
        s+=' | <a href="/admin/publicsite/event/'+str(ee.id)+'/" target="_blank">'+str(ee.entertainment)+' ('+str(ee.start_time)+')</a> ('
        for hh in ee.hosts.all()[0:4]:
            s+= hh.name + ", "
        s+='..)'
    
    return HttpResponse(s)


def admin_mergevenue(request, original):    
    from django.contrib.auth.decorators import login_required
    from django.db import connection, transaction 
    cursor = connection.cursor()
    login_required(admin_mergevenue)
    if request.POST['replaceid']:
        replacement = request.POST['replaceid']
    else:
        return HttpResponseRedirect('/admin/publicsite/venue/'+str(original))
    orig = Venue.objects.get(pk=original)
    replace = Venue.objects.get(pk=replacement)
    return HttpResponse("Venue " + replace.__str__() + " will replace " + orig.__str__() + " in " + str(orig.event_set.count()) + " parties. <a href=\"/accounts/replacevenue/"+str(original)+"/"+str(replacement)+"\">Click here to proceed</a>.")

def admin_mergevenue_confirmed(request, original, replacement):    
    from django.contrib.auth.decorators import login_required
    login_required(admin_mergevenue_confirmed)
    Event.objects.filter(venue=original).update(venue=replacement)
    orig = Venue.objects.get(pk=original).delete()
    return HttpResponseRedirect('/admin/publicsite/venue/')


def admin_mergelm(request, original):    
    from django.contrib.auth.decorators import login_required
    from django.db import connection, transaction 
    cursor = connection.cursor()
    login_required(admin_mergelm)
    if request.POST['replaceid']:
        replacement = request.POST['replaceid']
    else:
        return HttpResponseRedirect('/admin/publicsite/lawmaker/'+str(original))
    e = Event.objects.filter(beneficiaries=original)
    orig = Lawmaker.objects.get(pk=original)
    replace = Lawmaker.objects.get(pk=replacement)
    return HttpResponse("Lawmaker " + replace.__str__() + " will replace " + orig.__str__() + " in " + str(len(e)) + " parties. <a href=\"/accounts/replacelm/"+str(original)+"/"+str(replacement)+"\">Click here to proceed</a>.")

def admin_mergelm_confirmed(request, original, replacement):    
    from django.contrib.auth.decorators import login_required
    login_required(admin_mergelm_confirmed)
    from django.db import connection, transaction 
    cursor = connection.cursor()

    query = "UPDATE publicsite_event_beneficiary SET lawmaker_id="+str(replacement)+" WHERE lawmaker_id="+str(original)
    cursor.execute(query)
    query = "UPDATE publicsite_event_omc SET lawmaker_id="+str(replacement)+" WHERE lawmaker_id="+str(original)
    cursor.execute(query)
    orig = Lawmaker.objects.get(pk=original).delete()
    return HttpResponseRedirect('/admin/publicsite/lawmaker/')


"""
class PartyTimeLayar(LayarView):

    def get_partytime_queryset(self, latitude, longitude, radius, search_query,
                               **kwargs):
        deg_in_m = 111045.0

        width = radius / math.fabs(math.cos(math.radians(latitude))*deg_in_m)
        height = (radius / deg_in_m)
        latitude_range = (str(latitude-height), str(latitude+height))
        longitude_range = (str(longitude-width), str(longitude+width))
        venues = Venue.objects.filter(latitude__range=latitude_range,
                                      longitude__range=longitude_range)
        if search_query:
            venues = venues.filter(venue_name__icontains=search_query)

        return venues

    def poi_from_partytime_item(self, item):
        latest_event = Event.objects.filter(venue=item.id).select_related().order_by('-start_date')[0]

        venue_url = 'http://politicalpartytime.org/search/Venue_Name/%s/' % item.venue_name
        party_url = 'http://politicalpartytime.org/party/%s/' % latest_event.id
        actions = [{'label': 'See Venue', 'uri':venue_url},
                   {'label': 'Latest Party', 'uri': party_url}]

        line3 = ' '.join([str(l) for l in latest_event.beneficiaries.all()])

        return POI(id=item.id, lat=item.latitude, lon=item.longitude,
                   title=item.venue_name, line2=item.venue_address(),
                   line3=line3,
                   attribution='http://PoliticalPartyTime.org',
                   actions=actions)

partytime_layar = PartyTimeLayar()



class TownhouseLayar(PartyTimeLayar):

    def __init__(self):
        self.developer_key = ''

    def get_partytimetownhouses_queryset(self, latitude, longitude, radius, **kwargs):
        deg_in_m = 111045.0

        width = radius / math.fabs(math.cos(math.radians(latitude))*deg_in_m)
        height = (radius / deg_in_m)
        latitude_range = (str(latitude-height), str(latitude+height))
        longitude_range = (str(longitude-width), str(longitude+width))
        venues = Venue.objects.filter(latitude__range=latitude_range,
                                      longitude__range=longitude_range,
                                      townhouse=True)
        return venues

    def poi_from_partytimetownhouses_item(self, item):
        latest_event = Event.objects.filter(venue=item.id).select_related().order_by('-start_date')[0]

        venue_url = 'http://politicalpartytime.org/search/Venue_Name/%s/' % item.venue_name
        party_url = 'http://politicalpartytime.org/party/%s/' % latest_event.id
        actions = [{'label': 'See Venue', 'uri':venue_url},
                   {'label': 'Latest Party', 'uri': party_url}]

        return POI(id=item.id, lat=item.latitude, lon=item.longitude,
                   title=item.venue_name, line2=item.venue_address(),
                   attribution='http://PoliticalPartyTime.org',
                   actions=actions)


townhouse_layar = TownhouseLayar()

"""


def email_subscribe(request):
    """
    Confirmation URLs should look like:
    http://politicalpartytime.org/emailalerts?email=abycoffe@sunlightfoundation.com&confirmation=29083429309234&list=5

    The list number corresponds to the ID of the relevant MailingList object.
    """
    error_response = render_to_response('publicsite/message.html',
            {'message': 'There was an error. Please try your submission again.', })

    if request.method == 'POST': # User is subscribing to an e-mail list
        email = request.POST.get('email', None)
        list_id = request.POST.get('list', None)
        if not email or not list_id:
            #return HttpResponse('no email or list_id')
            return error_response

        email, created = Email.objects.get_or_create(email=email)

        if list_id == 'state':
            state = request.POST.get('state', None)
            if not state:
                return error_response
            mailing_list = get_object_or_404(MailingList, name=state)
        else:
            try:
                mailing_list = get_object_or_404(MailingList, id=list_id)
            except MailingList.DoesNotExist:
                return error_response


        confirmation = hash(str(email.pk + mailing_list.pk + random.randint(1, 999999999)))
        if confirmation < 0:
            confirmation = confirmation * -1

        try:
            membership = MailingListMembership.objects.create(mailing_list=mailing_list,
                                                              email=email,
                                                              confirmation=confirmation,
                                                              confirmed=False)
        except IntegrityError:
            return render_to_response('publicsite/message.html',
                    {'message': 'You are already subscribed to that mailing list. Please check your e-mail for instructions on confirming your subscription.', })

        membership.send_confirmation()
        return render_to_response('publicsite/message.html',
                {'message': 'Thank you for subscribing. Please check your e-mail for instructions on confirming your subscription.', })

    else:
        email = request.GET.get('email', None)
        list_id = request.GET.get('list', None)
        confirmation = request.GET.get('confirmation', None)
        if not email or not list_id or not confirmation:
            raise Http404

        mailing_list = get_object_or_404(MailingList, id=list_id)


        membership = get_object_or_404(MailingListMembership,
                                       mailing_list=mailing_list,
                                       #email=email,
                                       confirmation=confirmation)

        if 'remove' in request.GET:
            membership.delete()
            return render_to_response('publicsite/message.html',
                    {'message': 'You have been unsubscribed.', })

        membership.confirmed = True
        membership.save()

        return render_to_response('publicsite/message.html',
                {'message': 'Your subscription has been confirmed.', })


def venue_detail(request, venue_id):
    venue = get_object_or_404(Venue, pk=venue_id)
    return HttpResponseRedirect('/search/Venue_Name/%s' % venue.venue_name.replace(' ', '%20'))
