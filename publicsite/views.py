from django import forms
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core import serializers
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from partytime.publicsite.models import *
import random
import simplejson
import time
import datetime


from sunlightapi import sunlight, SunlightApiError
sunlight.apikey = '***REMOVED***'
#
# view methods
#

def index(request):
    now = datetime.datetime.now()
    blog_posts = Post.objects.filter(post_type='post').order_by('-post_date')[:10]
    return render_to_response('publicsite/index.html', {"blog_posts":blog_posts})
    
def party(request, docid): 
    doc = Event.objects.get(pk=docid)
    return render_to_response('publicsite/party.html', {"doc": doc}) 

def search_proxy(request):
    
    if request.method == "POST":
        
        field = request.POST.get('field', None)
        args = request.POST.get('args', None)
        
        if field and args:
            redirect_url = '/search/%s/%s/' % (field, args)
            return HttpResponseRedirect(redirect_url)

    return HttpResponseRedirect('/')
    
def search(request, field, args):
    events = Event.objects.by_field(field.lower(), args)
    return render_to_response('publicsite/search_results.html', {"field":field, "args":args, "docset":events})

def search_embed(request, field, args):
    events = Event.objects.by_field(field.lower(), args)
    return render_to_response('publicsite/search_embed.html', {"field":field, "args":args, "docset":events})


def convention_list(request, convention=''):
    
    if convention == 'republican':
        args = 'GOP convention'
    elif convention == 'democratic':
        args = 'Democratic convention'
    else:
        args = 'convention'
        
    events = Event.objects.filter(status='', tags__tag_name__icontains=args).exclude(start_date__isnull=True).order_by('start_date','start_time')
    
    return render_to_response('publicsite/search_results.html', {"field":"Tags", "args":args, "docset":events})

#
# upcoming and recent events
#

def recent(request):
    docset = Event.objects.recent(15)
    return render_to_response('publicsite/snapshot.html', {"snapshot_image_name":"recent", "docset":docset})

def upcoming(request):
    docset = Event.objects.upcoming(15)
    return render_to_response('publicsite/snapshot.html', {"snapshot_image_name":"upcoming", "docset":docset})

def upcoming_embed(request):
        docset = Event.objects.upcoming(5)
        return render_to_response('publicsite/upcoming_embed.html', {"snapshot_image_name":"upcoming", "docset":docset})


def bydate(request,start,end):
    docset = Event.objects.daterange(start,end)
    return render_to_response('publicsite/snapshot.html', {"snapshot_image_name":"", "docset":docset})

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
    
        events = Event.objects.filter(status='', tags__tag_name=arg)
        event_count = events.count()
        
        if event_count > 0:
            
            randdocnum = random.randint(0, event_count - 1)
            event = events[randdocnum]
            
            return render_to_response("publicsite/widgets/abc_convention.html",
                {"field":"Tags", "args": arg, "doc":event, "convention": convention})


def widget180_upcoming(request):
	events = Event.objects.filter(
					start_date__gte=datetime.datetime.now(),
					status='').exclude(entertainment="").order_by('start_date','start_time')[:3]
	return render_to_response('publicsite/widgets/widget_180.html', {"docset":events})



def leadpacs(request):
    from django.db import connection, transaction
    cursor = connection.cursor()
    rows = []
    try:
        cursor.execute("SELECT publicsite_lawmaker.name, publicsite_venue.venue_name, publicsite_event.start_date, publicsite_entertainment.entertainment_type, leadpacdistinct.pol, publicsite_event.id FROM ((publicsite_event_beneficiary INNER JOIN ((publicsite_venue INNER JOIN publicsite_event ON publicsite_venue.id = publicsite_event.venue_id) INNER JOIN publicsite_entertainment ON publicsite_event.entertainment_id = publicsite_entertainment.id) ON publicsite_event_beneficiary.event_id = publicsite_event.id) INNER JOIN publicsite_lawmaker ON publicsite_event_beneficiary.lawmaker_id = publicsite_lawmaker.id) INNER JOIN (SELECT DISTINCT pacname, pol FROM publicsite_leadpac) leadpacdistinct ON publicsite_lawmaker.name = leadpacdistinct.pacname WHERE (((publicsite_event.status) Is Null Or (publicsite_event.status)='')) ORDER BY publicsite_event.start_date DESC LIMIT 5;")
        rows = cursor.fetchall()      
    except:
        pass
    l = [] 
    for row in rows:
            l.append(row)                    
    return render_to_response('publicsite/leadpacs.html', {"docset":l[0:6]})

    
#
# file uploading
#

def upload(request):
    if request.method == 'POST' and request.FILES:
        uf = request.FILES.get('pdf', None)
        if uf:
            if uf.name.endswith(".pdf") and uf.size < 1024 * 1024 * 100:    # size < 100MB
                path = "%s/upload/%s.pdf" % (settings.FILE_UPLOAD_PATH, random.randint(100000,999999))
                destination = open(path, 'wb')
                for chunk in uf.chunks():
                    destination.write(chunk)
                    return HttpResponseRedirect('/upload/thanks/')
    return render_to_response('publicsite/upload.html')
    
def upload_thanks(request):
    return HttpResponse("thanks")


#committees .... added by luke rosiak 5/27
def cmtes(request, chamber='House'):
    clist = Committee.objects.filter(chamber=chamber)
    res = clist
   
    from django.db import connection, transaction 
    cursor = connection.cursor()
    cursor.execute("SELECT i.cn, count(i.co) FROM (SELECT DISTINCT cm.committee_id cn, e.id co FROM publicsite_event e INNER JOIN publicsite_event_beneficiary b ON (e.id=b.event_id) INNER JOIN publicsite_lawmaker l ON (l.id=b.lawmaker_id) INNER JOIN publicsite_committee_members cm ON (l.id=cm.lawmaker_id) WHERE (e.status is null or e.status='') AND YEAR(e.start_date)>=2009 GROUP BY cm.committee_id, e.id) i GROUP BY cn;")
    summary = cursor.fetchall()
     
    return render_to_response('publicsite/cmte.html', {"res": res, "chamber": chamber, "summary": summary }) #res = list of {"cmte": cmte, "events": ev, "nummems": len(SunLeg) } 


def cmtedetail(request, cmteid):
    res = Event.objects.by_cmte(cmteid)
    docset = res['events']

    from django.db import connection, transaction 
    cursor = connection.cursor()
    cursor.execute("SELECT lq.id, lq.name, count(ev)  FROM (SELECT l.id, l.name, e.id ev FROM publicsite_event e INNER JOIN publicsite_event_beneficiary b ON (e.id=b.event_id) INNER JOIN publicsite_lawmaker l ON (l.id=b.lawmaker_id) INNER JOIN publicsite_committee_members cm ON (l.id=cm.lawmaker_id AND cm.committee_id='"+cmteid+"') WHERE (e.status is null or e.status='') AND YEAR(e.start_date)>=2009 GROUP BY l.id, l.name, ev) lq GROUP BY lq.id, lq.name;")
    summary = cursor.fetchall()

    return render_to_response('publicsite/cmtedetail.html', {"cmte": res['cmte'], "docset":res['events'], "members": res['members'], "summary": summary, "since_year": res['since_year'] })


def updatecmtes(request,chamber):
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



#data dump

def dump_all(request):
    from django.db import connection, transaction
    from django.utils.encoding import smart_str, smart_unicode
    import csv

    cursor = connection.cursor()

    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename=party_dumpall.csv'
    writer = csv.writer(response)

    # Data retrieval operation - no commit required
    try:
        cursor.execute("SELECT pe.id _id,ifnull(group_concat(distinct pb.name, IF(STRCMP(pb.party,''),' (',''),pb.party,IF(STRCMP(pb.state,''),', ',''),pb.state,IF(STRCMP(pb.district,''),concat('-',pb.district),'') , IF(STRCMP(pb.party,''),')','') separator ' || ' ),'') beneficiary,ifnull(group_concat(distinct thost.name separator ' || '),'') host,ifnull(group_concat(distinct  omcl.name, IF(STRCMP(omcl.party,''),' (',''),omcl.party,IF(STRCMP(omcl.state,''),', ',''),omcl.state,IF(STRCMP(omcl.district,''),concat('-',omcl.district),'') , IF(STRCMP(omcl.party,''),')','') separator ' || ' ),'') Other_Members_of_Congress, IFNULL(DATE_FORMAT(start_date,'%%m/%%d/%%Y'),'') Start_Date,IFNULL(DATE_FORMAT(end_date,'%%m/%%d/%%Y'),'') End_Date,IFNULL(DATE_FORMAT(Start_Time,'%%l:%%i %%p'),'') Start_Time,IFNULL(DATE_FORMAT(end_time,'%%l:%%i %%p'),'') End_Time,  entertainment_type,venue_name,address1,address2,city,v.state,zipcode,website,concat(ifnull(v.latitude,''),';',ifnull(v.longitude,'')) LatLong,Contributions_Info,Make_Checks_Payable_To,Checks_Payable_To_Address,Committee_Id,RSVP_Info,Distribution_Paid_for_By, ifnull(group_concat(distinct ttag.tag_name separator ' || '),'') tags  FROM publicsite_event pe left join publicsite_event_beneficiary peb on (peb.event_id = pe.id) left join publicsite_lawmaker pb on (peb.lawmaker_id = pb.id) left join publicsite_venue v on (v.id = pe.venue_id)  left join publicsite_entertainment et on (et.id = pe.entertainment_id) left join publicsite_event_omc tomc on (tomc.event_id = pe.id) left join publicsite_lawmaker omcl on (tomc.lawmaker_id = omcl.id) left join publicsite_event_hosts ev_hosts on (ev_hosts.event_id = pe.id) left join publicsite_host thost on (ev_hosts.host_id = thost.id)  left join publicsite_event_tags evtags on (evtags.event_id = pe.id) left join publicsite_tags ttag on (evtags.tag_id = ttag.id) WHERE (pe.status=null OR pe.status='') GROUP BY pe.id")

    except:
        pass

    newrow = ['ID', 'Beneficiary', 'Host', 'Other Members', 'Start_Date', 'End_Date', 'Start_Time', 'End_Time',	'Entertainment_Type', 'Venue_Name',	'Venue_Address1', 'Venue_Address2', 'Venue_City', 'Venue_State', 'Venue_Zipcode', 'Venue_Website', 'LatLong', 'Contributions_Info',	'Make_Checks_Payable_To', 'Checks_Payable_To_Address', 'Committee_Id', 'RSVP_Info', 'Distribution_Paid_for_By', 'Tags'];		
    newrowt = ['key', 'Beneficiary', 'Host', 'Other Members', 'Start_Date', 'End_Date', 'Start_Time', 'End_Time',	'Entertainment_Type', 'Venue_Name',	'Venue_Address1', 'Venue_Address2', 'Venue_City', 'Venue_State', 'Venue_Zipcode', 'Venue_Website', 'LatLong', 'Contributions_Info',	'Make_Checks_Payable_To', 'Checks_Payable_To_Address', 'Committee_Id', 'RSVP_Info', 'Distribution_Paid_for_By', 'Tags'];																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																		
    writer.writerow(newrowt)
    rows = cursor.fetchall()
    for row in rows:
        newrow = []
        for nr in row:
            newrow.append( smart_str(nr) )
        writer.writerow(newrow)


    return response


def dump_mult(request):
    from django.db import connection, transaction
    from django.utils.encoding import smart_str, smart_unicode
    import csv
    import zipfile
    from cStringIO import StringIO

    cursor = connection.cursor()

    zbuffer = StringIO()
    fbuffer = StringIO()
    zfile = zipfile.ZipFile(zbuffer, "w", zipfile.ZIP_DEFLATED)
    response = HttpResponse(mimetype='application/zip')
    response['Content-Disposition'] = 'filename=party_dumpmult.zip'

    #EVENT TABLE
    writer = csv.writer(fbuffer)

    try:
        cursor.execute("SELECT pe.id _id,IFNULL(DATE_FORMAT(start_date,'%%m/%%d/%%Y'),'') Start_Date,IFNULL(DATE_FORMAT(end_date,'%%m/%%d/%%Y'),'') End_Date,IFNULL(DATE_FORMAT(Start_Time,'%%l:%%i %%p'),'') Start_Time,IFNULL(DATE_FORMAT(end_time,'%%l:%%i %%p'),'') End_Time,  entertainment_type,venue_name,address1,address2,city,v.state,zipcode,website,concat(ifnull(v.latitude,''),';',ifnull(v.longitude,'')) LatLong,Contributions_Info,Make_Checks_Payable_To,Checks_Payable_To_Address,Committee_Id,RSVP_Info,Distribution_Paid_for_By, ifnull(group_concat(distinct ttag.tag_name separator ' || '),'') tags  FROM publicsite_event pe left join publicsite_venue v on (v.id = pe.venue_id)  left join publicsite_entertainment et on (et.id = pe.entertainment_id)  left join publicsite_event_tags evtags on (evtags.event_id = pe.id) left join publicsite_tags ttag on (evtags.tag_id = ttag.id) WHERE (status='' or status is null)  group by pe.id")
    except:
        pass
    rows = cursor.fetchall()
    newrow =["_id","Start_Date","End_Date","Start_Time","End_Time","Entertainment_Type","Venue_Name","Venue_Address1","Venue_Address2","Venue_City","Venue_State","Venue_Zipcode","Venue_Website","LatLong","Contributions_Info","Make_Checks_Payable_To","Checks_Payable_To_Address","Committee_Id","RSVP_Info","Distribution_Paid_for_By","Tags"]																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																			
    writer.writerow(newrow)
    for row in rows:
        newrow = []
        for nr in row:
            newrow.append( smart_str(nr) )
        writer.writerow(newrow)

    zfile.writestr('events.csv', fbuffer.getvalue())
    fbuffer.close()

    #BENEFICIARIES TABLE
    fbuffer2 = StringIO()
    writer = csv.writer(fbuffer2)
    try:
        cursor.execute("SELECT eb.event_id,l.id beneficiary_id, ifnull(name,'') Beneficiary_Name,ifnull(party,'') party, ifnull(state,'') state, ifnull(district,'') district, oi.other_info, crp_id FROM publicsite_event_beneficiary eb left join publicsite_lawmaker l on (l.id = eb.lawmaker_id)  left join publicsite_other_info oi on (oi.event_id = eb.event_id and oi.lawmaker_id = eb.lawmaker_id and oi.moc_type=1) left join publicsite_event ev ON (eb.event_id=ev.id AND (ev.status is null or ev.status='')) order by eb.event_id")
    except:
        pass
    rows = cursor.fetchall()
    newrow = ["event_id","beneficiary_id","Beneficiary_Name","Party","State","District","Other_Info","CRP_id"]																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																								
    writer.writerow(newrow)
    for row in rows:
        newrow = []
        for nr in row:
            newrow.append( smart_str(nr) )
        writer.writerow(newrow)

    zfile.writestr('beneficiaries.csv', fbuffer2.getvalue())
    fbuffer2.close()

 
    #HOSTS TABLE
    fbuffer3 = StringIO()
    writer = csv.writer(fbuffer3)
    try:
        cursor.execute("SELECT eh.event_id,h.id host_id, ifnull(name,'') Host_Name,ifnull(other_info,'') Other_Info FROM publicsite_event_hosts eh left join publicsite_host h on (h.id = eh.host_id)  left join publicsite_other_info oi on (oi.event_id = eh.event_id and oi.host_id = eh.host_id) left join publicsite_event ev ON (eh.event_id=ev.id AND (ev.status is null or ev.status='')) order by eh.event_id")
    except:
        pass
    rows = cursor.fetchall()
    newrow =   ["event_id","host_id","Host_Name","Other_Info"]																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																			
    writer.writerow(newrow)
    for row in rows:
        newrow = []
        for nr in row:
            newrow.append( smart_str(nr) )
        writer.writerow(newrow)

    zfile.writestr('hosts.csv', fbuffer3.getvalue())
    fbuffer3.close()


    #OMCS TABLE
    fbuffer4 = StringIO()
    writer = csv.writer(fbuffer4)
    try:
        cursor.execute("SELECT eb.event_id,l.id omc_id, ifnull(name,'') OMC_Name,ifnull(party,'') party, ifnull(state,'') state, ifnull(district,'') district,ifnull(other_info,'') Other_Info,crp_id FROM publicsite_event_omc  eb left join publicsite_lawmaker l on (l.id = eb.lawmaker_id) left join publicsite_other_info oi on (oi.event_id = eb.event_id and oi.lawmaker_id = eb.lawmaker_id and oi.moc_type=2) left join publicsite_event ev ON (eb.event_id=ev.id AND (ev.status is null or ev.status=''))  order by eb.event_id")
    except:
        pass
    rows = cursor.fetchall()
    newrow = ["event_id","omc_id","OMC_Name","Party","State","District","Other_Info","CRP_id"]																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																			
    writer.writerow(newrow)
    for row in rows:
        newrow = []
        for nr in row:
            newrow.append( smart_str(nr) )
        writer.writerow(newrow)

    zfile.writestr('omcs.csv', fbuffer4.getvalue())
    fbuffer4.close()


    #VENUES TABLE
    fbuffer5 = StringIO()
    writer = csv.writer(fbuffer5)
    try:
        cursor.execute("SELECT id, ifnull(venue_name,'') venue_name,ifnull(venue_address,'') venue_address,address1,address2,city,state,zipcode, ifnull(latitude,'') latitude,ifnull(longitude,'') longitude,website FROM publicsite_venue order by venue_address")
    except:
        pass
    rows = cursor.fetchall()
    newrow = ["id","venue_name","venue_address","Venue_Address1","Venue_Address2","Venue_City","Venue_State","Venue_Zipcode","latitude","longitude","Venue_Website"]		
    newrowt = ["key","venue_name","venue_address","Venue_Address1","Venue_Address2","Venue_City","Venue_State","Venue_Zipcode","latitude","longitude","Venue_Website"]																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																			
																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																	
    writer.writerow(newrowt)
    for row in rows:
        newrow = []
        for nr in row:
            newrow.append( smart_str(nr) )
        writer.writerow(newrow)

    zfile.writestr('venues.csv', fbuffer5.getvalue())
    fbuffer5.close()

    zfile.close()
    zbuffer.flush()
    ret_zip = zbuffer.getvalue()
    response.write(ret_zip)
    zbuffer.close()
    return response



