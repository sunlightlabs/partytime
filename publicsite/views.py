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
    blog_posts = Post.objects.filter(post_type='post', post_status='publish').order_by('-post_date')[:10]
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
    lm = None
    if field == 'Beneficiary':
        lm = Lawmaker.objects.filter(name__icontains=args)
        if len(lm)==1:
            if lm[0].crp_id and lm[0].affiliate==None:
                return HttpResponseRedirect('/pol/'+lm[0].crp_id)               
    if lm!=None:
        lm = lm.filter(affiliate=None).exclude(crp_id=None)
    events = Event.objects.by_field(field.lower(), args)

    return render_to_response('publicsite/search_results.html', {"field":field, "args":args, "docset":events, "lm": lm})

def search_embed(request, field, args):
    events = Event.objects.by_field(field.lower(), args)
    return render_to_response('publicsite/search_embed.html', {"field":field, "args":args, "docset":events})

def search_embed_flex(request, field, args):
        events = Event.objects.by_field(field.lower(), args).order_by('start_date')[:3]
        return render_to_response('publicsite/search_embed_flex.html', {"field":field, "args":args, "docset":events})


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

def upcoming_embed2(request):
        docset = Event.objects.upcoming(5)
        return render_to_response('publicsite/upcoming_embed_2.html', {"snapshot_image_name":"upcoming", "docset":docset})

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



def leadpac_all(request):
    docset = Event.objects.filter(status='', beneficiaries__affiliate__isnull=False).order_by('-start_date','-start_time')
    return render_to_response('publicsite/snapshot.html', {"snapshot_image_name":"", "docset":docset})

def leadpacs(request):
    docset = Event.objects.filter(status='', beneficiaries__affiliate__isnull=False).order_by('-start_date','-start_time')[0:6]       
    return render_to_response('publicsite/leadpacs.html', {"docset":docset})


#added 7/29 for lawmaker search including leadpac
def polwithpac(request, cid):
    lm=None
    pacname=None
    polname=None
    l = Lawmaker.objects.filter(crp_id=cid).distinct()
    if len(l)==0:
        return HttpResponseRedirect('/')     
    for ll in l:
        if ll.affiliate:
            pacname = ll.name
        else:
            lm = ll
      
    eventlist = Event.objects.filter(status='', beneficiaries__crp_id=cid).order_by('-start_date','-start_time')
    return render_to_response('publicsite/polwithpac.html', {"eventlist":eventlist, "lm": lm, "pacname": pacname })
    
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




