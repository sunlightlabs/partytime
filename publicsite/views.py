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
					status='').exclude(entertainment_type="").order_by('start_date','start_time')[:3]
	return render_to_response('publicsite/widgets/widget_180.html', {"docset":events})


    
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
    #Cmtes = Committee.objects.all()
    Cmtes = sunlight.committees.getList(chamber)   
    res = []
    for c in Cmtes:
	res.append(  Event.objects.by_cmte(c.id) )
    return render_to_response('publicsite/cmte.html', {"res": res, "chamber": chamber }) #res = list of {"cmte": cmte, "events": ev, "nummems": len(SunLeg) } 

#def cmtedetail(request, cmteid):
#    cmte = sunlight.committees.get(cmteid)
#    SunLeg = cmte.members
#    Mems = []
#    for m in SunLeg:
#        for e in Event.objects.filter(beneficiaries__crp_id = m.crp_id):
#		Mems.append(e)
    #Mems = Lawmaker.objects.all()
#    return render_to_response('publicsite/cmtedetail.html', {"mems": Mems, "cmte": cmte, "sunleg": SunLeg }) 

def cmtedetail(request, cmteid):
    res = Event.objects.by_cmte(cmteid)
    docset = res['events']
    cmte = res['cmte'] #sunlight.committees.get(cmteid)
    mems = cmte.members
    return render_to_response('publicsite/cmtedetail2.html', {"cmte": cmte, "docset":docset, "mems": mems, "since_year": res['since_year'] })

