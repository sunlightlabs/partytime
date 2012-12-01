import datetime, re

from django.template import Library
from django.db.models import Count, Sum, Q
from django.template.defaultfilters import stringfilter

from publicsite.models import * 


register = Library()

# customize month names. Oye. 
month_name_array = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'June', 'July', 'Aug', 'Sept','Oct', 'Nov', 'Dec']

@register.inclusion_tag('publicsite_redesign/templatetag_templates/partystats.html')  
def partystats():
    """ Calculate all the stuff needed for the footer -- which also appears out of the footer on the index page. """
    today = datetime.date.today()
    year = today.year
    month = today.month
    dayofweek = today.weekday() + 1 # Fix to make Sunday = 0
    
    yearstart = "%s0101" % year
    yearend = "%s1231" % year
    
    monthstart = "%s%s01" % (year, month)
    nextmonthstart = "%s%s01" % (year, month+1)
    
    parties_this_year = Event.objects.daterange(yearstart, yearend)
    
    presidential_parties = parties_this_year.filter(is_presidential=True)
    
    # somehow ordering by allows the list to be truly unique. 
    hosts = len(parties_this_year.filter(hosts__isnull=False).order_by('beneficiaries').distinct().values_list('hosts'))
    beneficiaries = len(parties_this_year.order_by('beneficiaries').distinct().values_list('beneficiaries'))

    parties_this_month =  Event.objects.month(year,month)
    
    weekstart = today - datetime.timedelta(days=dayofweek)
    weekend = today + datetime.timedelta(days= (6-dayofweek) )

    weekstartstring = weekstart.strftime("%Y%m%d")
    weekendstring = weekend.strftime("%Y%m%d")
    parties_this_week = Event.objects.daterange(weekstartstring, weekendstring)

    num_parties_this_year = parties_this_year.aggregate(total=Count('pk'))['total']
    num_parties_this_month = parties_this_month.aggregate(total=Count('pk'))['total']
    num_parties_this_week = parties_this_week.aggregate(total=Count('pk'))['total']
    num_presidential_parties = presidential_parties.aggregate(total=Count('pk'))['total']
    
    return {
        'parties_this_year': num_parties_this_year,
        'parties_this_month':num_parties_this_month,
        'parties_this_week':num_parties_this_week,
        'num_presidential_parties':num_presidential_parties,
        'hosts':hosts,
        'beneficiaries':beneficiaries,
    }
    

@register.inclusion_tag('publicsite_redesign/templatetag_templates/sidebarcontent.html')  
def sidebarcontent():
    
    newest_events = Event.objects.newest(3)
    upcoming_events = Event.objects.upcoming(3)
    recent_events = Event.objects.recent(3)

    return {
    'newest_events':newest_events,
    'upcoming_events':upcoming_events,
    'recent_events':recent_events
    }

@register.inclusion_tag('publicsite_redesign/templatetag_templates/eventitem.html')
def renderevent(event, new_window=False):
    """ Kick this all out to a common template """
    return{
    'event':event,
    'new_window':new_window,
    }
    
  

@register.inclusion_tag('publicsite_redesign/templatetag_templates/indexpage_partylist.html')
def partiesheldforleadership():
    title = "Parties Held for Congressional Leadership"
    viewmorelink = "/congressional-leadership/"
    today = datetime.date.today()

    # what's the timing of all this stuff? 
    leader_ids = LeadershipPosition.objects.values_list('lawmaker_id', flat=True)
    events = Event.objects.filter(status="", beneficiaries__pk__in=leader_ids, start_date__lte=today).distinct().order_by('-start_date', 'start_time')
    
    parties = events[:3]
    
    return{
    'parties':parties,
    'title':title,
    'viewmorelink':viewmorelink,
    }
    
@register.inclusion_tag('publicsite_redesign/templatetag_templates/indexpage_partylist.html')
def partiesheldforcommitteeleadership():
    title = "Parties Held for Committee<br>Leadership"
    viewmorelink = "/committee-leadership/"
    today = datetime.date.today()

    # what's the timing of all this stuff? 
    crp_ids = list(CommitteeMembership.objects.values_list('member__crp_id', flat=True).exclude(position='Member'))
    leadership_ids = list(Lawmaker.objects.filter(crp_id__in=crp_ids).values_list('id', flat=True))

    events = Event.objects.filter(status="", beneficiaries__in=leadership_ids, start_date__lte=today).distinct().order_by('-start_date', 'start_time')

    parties = events[:3]

    return{
    'parties':parties,
    'title':title,
    'viewmorelink':viewmorelink,
    }
    
@register.inclusion_tag('publicsite_redesign/templatetag_templates/indexpage_partylist.html')
def partieshostedbyleadership():
    title = "Parties Hosted by Congressional Leadership"
    viewmorelink = "/hosted-by-congressional-leadership/"
    today = datetime.date.today()

    # what's the timing of all this stuff? 
    leader_ids = LeadershipPosition.objects.values_list('lawmaker__crp_id', flat=True)
    events = Event.objects.filter(status="", other_members__crp_id__in=leader_ids, start_date__lte=today).distinct().order_by('-start_date', 'start_time')

    parties = events[:3]
    #print parties

    return{
    'parties':parties,
    'title':title,
    'viewmorelink':viewmorelink,
    }    
    
    
@register.inclusion_tag('publicsite_redesign/templatetag_templates/indexpage_partylist.html')
def partiesforpresidentialcandidates():
    title = "Parties Held For Presidential<br>Candidates"
    viewmorelink = "/presidential/"
    today = datetime.date.today()
    
    parties = Event.objects.presidential(3)
    #print parties

    return{
    'parties':parties,
    'title':title,
    'viewmorelink':viewmorelink,
    }    
    
@register.inclusion_tag('publicsite_redesign/templatetag_templates/indexpage_partylist.html')
def partiesfor2013inauguration():
    title = "Parties Held For<br>The 2013<br>Inauguration"
    query = '2013 Inauguration'
    viewmorelink = "/search-all/?q=2013+Inauguration"
    # put newest added first so the home page doesn't look static
    parties =  Event.objects.filter(entertainment__icontains=query).order_by('-added')[:3]
    #print parties

    return{
    'parties':parties,
    'title':title,
    'viewmorelink':viewmorelink,
    }
        
@register.inclusion_tag('publicsite_redesign/templatetag_templates/year_in_parties.js')
def yearinpartiesjs():
    
    today = datetime.date.today()
    year = today.year
    month = today.month
    next_month = ( month + 1) % 12
    next_year_maybe = year + ( month + 1) / 12 # these are ints so this works.
    startdate = datetime.date(year-1, month, 1)
    enddate = datetime.date(next_year_maybe, next_month, 1)
    events = Event.objects.filter(
                start_date__gte=startdate, start_date__lt=enddate,
                status='')
    
    
    monthly_count = events.extra(select={'year': 'EXTRACT(year FROM start_date)','month': 'EXTRACT(month FROM start_date)'}).values_list('year', 'month').order_by('year', 'month').annotate(Count('pk'))
    month_data = []
    month_names = []

    
    for month in monthly_count:

        month_datum = {
        'count':month[2]
        }
        month_name = {
        'name':month_name_array[int(month[1])]
        }
        month_data.append(month_datum)
        month_names.append(month_name)
        
            
    return{
    'month_data':month_data,
    'month_names':month_names
    }

# prints a list of days 
def get_date_list(start_date, end_date):
    if end_date <= start_date:
        raise Exception("End date must be less than start date")
    this_date = start_date
    results = []
    while (this_date <= end_date):
        results.append(this_date)
        this_date = this_date + datetime.timedelta(days=1)
    return results
    
# It's really three weeks in parties, because we gotta show the preceding weeks as well
@register.inclusion_tag('publicsite_redesign/templatetag_templates/week_in_parties.js')
def weekinpartiesjs(startingdate):
    # start date is YYYYMMDD of the start date of the week--but we really want to start almost one week before the week starts--and end almost one week *after* the week ends. Hence:
    startdate = datetime.date(int(startingdate[0:4]), int(startingdate[4:6]), int(startingdate[6:8]))
    realstart = startdate - datetime.timedelta(days=6)
    realend = startdate + datetime.timedelta(days=13)
    dates = get_date_list(realstart, realend)
    
    # get the count of parties during this time period. We still have to account for days where there are no parties though.
    
    date_summary = Event.objects.daterange(realstart.strftime("%Y%m%d"), realend.strftime("%Y%m%d")).extra(select={'year': 'EXTRACT(year FROM start_date)','month': 'EXTRACT(month FROM start_date)','day': 'EXTRACT(day FROM start_date)'}).values_list('year', 'month', 'day').order_by('year', 'month', 'day').annotate(Count('pk'))
    #print date_summary
    
    # hash it
    summary_dict = {}
    for date in date_summary:
        this_date_string = "%s%s%s" % (date[0], date[1], date[2])
        summary_dict[this_date_string]=date[3]
    
    #print summary_dict
    
    data_dict = []
    for day in dates:
    
        year = day.strftime("%Y") 
        month =  int(day.strftime("%m"))
        day = int(day.strftime("%e"))
        date_key = "%s%s%s" % (year, month, day)
        this_sum = 0
        #print "'%s'" % (date_key)
        try:
            this_sum = summary_dict[date_key]
        except KeyError:
            pass
        data_dict.append(this_sum)
        
    #print data_dict
                
            
    return{
       'dates':dates,
       'data_dict':data_dict,
    }
    
@register.filter
@stringfilter
def highlightsearchterm(value, searchterm):
    # Ignore case in return emphasis
    search_regex = re.compile(r"(" + re.escape(searchterm) + r")", re.I)
    result = re.sub(search_regex, r'<em>\1</em>', value)
    return result
    
