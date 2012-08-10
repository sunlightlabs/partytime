import datetime

from django.template import Library
from django.db.models import Count, Q

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
    dayofweek = today.weekday() # 0 = Sunday
    
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
def renderevent(event):
    """ Kick this all out to a common template """
    return{
    'event':event,
    }

@register.inclusion_tag('publicsite_redesign/templatetag_templates/indexpage_partylist.html')
def partiesheldforleadership():
    title = "Parties Held for Congressional Leadership"
    viewmorelink = ""

    # what's the timing of all this stuff? 
    leader_ids = LeadershipPosition.objects.values_list('lawmaker_id', flat=True)
    events = Event.objects.filter(status="", beneficiaries__pk__in=leader_ids).distinct().order_by('-start_date', 'start_time')
    
    parties = events[:3]
    
    return{
    'parties':parties,
    'title':title,
    'viewmorelink':viewmorelink,
    }
    
@register.inclusion_tag('publicsite_redesign/templatetag_templates/indexpage_partylist.html')
def partiesheldforcommitteeleadership():
    title = "Parties Held for Committee<br>Leadership"
    viewmorelink = ""

    # what's the timing of all this stuff? 
    crp_ids = list(CommitteeMembership.objects.values_list('member__crp_id', flat=True).exclude(position='Member'))
    leadership_ids = list(Lawmaker.objects.filter(crp_id__in=crp_ids).values_list('id', flat=True))

    events = Event.objects.filter(status="", beneficiaries__in=leadership_ids).distinct().order_by('-start_date', 'start_time')

    parties = events[:3]

    return{
    'parties':parties,
    'title':title,
    'viewmorelink':viewmorelink,
    }
    
@register.inclusion_tag('publicsite_redesign/templatetag_templates/indexpage_partylist.html')
def partieshostedbyleadership():
    title = "Parties Hosted by Congressional Leadership"
    viewmorelink = ""

    # what's the timing of all this stuff? 
    leader_ids = LeadershipPosition.objects.values_list('lawmaker__crp_id', flat=True)
    events = Event.objects.filter(status="", other_members__crp_id__in=leader_ids).distinct().order_by('-start_date', 'start_time')

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
    viewmorelink = ""

    events = Event.objects.filter(status="", is_presidential=True).distinct().order_by('-start_date', 'start_time')

    parties = events[:3]
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
    
    startdate = datetime.date(year-1, month, 1)
    enddate = datetime.date(year, month+1, 1)
    events = Event.objects.filter(
                start_date__gte=startdate, start_date__lt=enddate,
                status='')
    
    
    monthly_count = events.extra(select={'year': 'EXTRACT(year FROM start_date)','month': 'EXTRACT(month FROM start_date)'}).values_list('year', 'month').order_by('year', 'month').annotate(Count('pk'))
    
    month_data = []
    month_names = []

    
    for month in monthly_count:
        #print month, int(month[1]), month[2]
        #print 
        month_datum = {
        'count':month[2]
        }
        month_name = {
        'name':month_name_array[int(month[1])]
        }
        month_data.append(month_datum)
        month_names.append(month_name)
        
    print month_data, month_names
            
    return{
    'month_data':month_data,
    'month_names':month_names
    }



