import math
import random
import simplejson
import time
import datetime

from django import forms
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core import serializers
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.db.models.query import QuerySet
from django.utils.encoding import smart_str

from partytime.publicsite.models import *
from layar import LayarView, POI


#
# view methods
#

def index(request):
    term=None
    now = datetime.datetime.now()
    if request.method == "POST":
        term = request.POST.get('term', None)
    if request.method == "GET":
        term = request.GET.get('term', None)
    if term:        
        blog_posts = Post.objects.filter(post_type='post', post_status='publish', content__icontains=term).order_by('-post_date')[:10]
    else:
        blog_posts = Post.objects.filter(post_type='post', post_status='publish').order_by('-post_date')[:10]
    return render_to_response('publicsite/index.html', {"blog_posts":blog_posts}, context_instance=RequestContext(request))


    
def party(request, docid): 
    try:
        doc = Event.objects.get(pk=docid)
    except:
        return HttpResponseRedirect('/')
    return render_to_response('publicsite/party.html', {"doc": doc}) 

def search_proxy(request):
    
    if request.method == "POST":        
        field = request.POST.get('field', None)
        args = request.POST.get('args', None)
    if request.method == "GET":
        field = request.GET.get('field', None)
        args = request.GET.get('args', None)     
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

    return render_to_response('publicsite/search_results.html', {"field":field, "args":args, "docset":events, "lm": lm}, context_instance=RequestContext(request))

def search_embed(request, field, args):
    events = Event.objects.by_field(field.lower(), args)
    return render_to_response('publicsite/search_embed.html', {"field":field, "args":args, "docset":events}, context_instance=RequestContext(request))

def search_embed_flex(request, field, args):
        events = Event.objects.by_field(field.lower(), args).order_by('start_date')[:3]
        return render_to_response('publicsite/search_embed_flex.html', {"field":field, "args":args, "docset":events}, context_instance=RequestContext(request))


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


def jsonCID(request, CID):
    from django.core import serializers
    events = Event.objects.filter( beneficiaries__crp_id=CID, status='').order_by('start_date','start_time')
    try:
        data = serializers.serialize("json", events, fields=('committee_id','start_date','start_time','entertainment','venue','contributions_info','hosts','beneficiaries','make_checks_payable_to'), use_natural_keys=True)
    except:
        data = ''    
    return HttpResponse(data)





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
    return render_to_response('publicsite/upload.html', context_instance=RequestContext(request))
    
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



#lobbyists .... added by luke rosiak 9/16
def lobby(request, level="ind"):
    from django.db import connection, transaction 
    cursor = connection.cursor()
    if level=='ind':
        query = "SELECT catname, realcode, count(id) c FROM (SELECT publicsite_crp_category.catname, publicsite_crp_category.realcode, publicsite_event.id FROM (((publicsite_crp_lobbying INNER JOIN publicsite_host ON publicsite_crp_lobbying.datekey = publicsite_host.crp_id) INNER JOIN publicsite_event_hosts ON publicsite_host.id = publicsite_event_hosts.host_id) INNER JOIN publicsite_event ON publicsite_event_hosts.event_id = publicsite_event.id) INNER JOIN publicsite_crp_category ON publicsite_crp_lobbying.realcode = publicsite_crp_category.realcode WHERE (((publicsite_event.status) Is Null Or (publicsite_event.status)='')) GROUP BY publicsite_crp_category.catname, publicsite_crp_category.realcode, publicsite_event.id ) a GROUP BY catname ORDER BY c DESC"
    elif level=='person':
        query = "SELECT publicsite_host.name, publicsite_host.crp_id, Count(publicsite_event.id) c FROM (publicsite_host INNER JOIN publicsite_event_hosts ON publicsite_host.id = publicsite_event_hosts.host_id) INNER JOIN publicsite_event ON publicsite_event_hosts.event_id = publicsite_event.id WHERE (((publicsite_event.status) Is Null Or (publicsite_event.status)='') AND ((publicsite_host.crp_id) Is Not Null)) GROUP BY publicsite_host.name, publicsite_host.crp_id HAVING c>2 ORDER BY Count(publicsite_event.id) DESC;"
    else:
        level = "corp"
        query = "SELECT org, o2, count(id) c FROM (SELECT publicsite_crp_lobbying.org, publicsite_crp_lobbying.org o2, publicsite_event.id FROM (((publicsite_crp_lobbying INNER JOIN publicsite_host ON publicsite_crp_lobbying.datekey = publicsite_host.crp_id) INNER JOIN publicsite_event_hosts ON publicsite_host.id = publicsite_event_hosts.host_id) INNER JOIN publicsite_event ON publicsite_event_hosts.event_id = publicsite_event.id)  WHERE (((publicsite_event.status) Is Null Or (publicsite_event.status)='')) GROUP BY publicsite_crp_lobbying.org, o2, publicsite_event.id) a GROUP BY org, o2 ORDER BY c DESC;"

    cursor.execute(query)
    summary = cursor.fetchall()
     
    return render_to_response('publicsite/lobby.html', {"summary": summary, "level": level }) 


def lobbydetail(request, category):
    #from django.db.models import *
    from django.db import connection, transaction 
    cursor = connection.cursor()

    cat = Crp_category.objects.get(realcode=category)

    """get list of lobbyists and who they're representing, in this industry"""
    #hostset = Host.objects.filter(crp_lobbying__category=category)
    query = "SELECT publicsite_crp_lobbying.org, publicsite_host.name, publicsite_host.crp_id FROM ((publicsite_host INNER JOIN publicsite_crp_lobbying ON publicsite_host.crp_id = publicsite_crp_lobbying.datekey) INNER JOIN publicsite_event_hosts ON publicsite_host.id = publicsite_event_hosts.host_id) INNER JOIN publicsite_event ON publicsite_event_hosts.event_id = publicsite_event.id WHERE (((publicsite_event.status) Is Null Or (publicsite_event.status)='') AND ((publicsite_crp_lobbying.realcode)='"+category+"')) GROUP BY publicsite_crp_lobbying.org, publicsite_host.name, publicsite_host.crp_id ORDER BY publicsite_crp_lobbying.org, publicsite_host.name;"
    cursor.execute(query)
    lobset = cursor.fetchall()

    corps = []
    for l in lobset:
        isin=False
        for c in corps:
            if c['org']==l[0]:
                c['lobbyists'].append( (l[1], l[2])  )
                isin=True
        if isin==False:
            corps.append( { "org": l[0], "lobbyists": [(l[1], l[2])] } )


    """get list of party beneficiaries"""
    query = "SELECT publicsite_event_beneficiary.lawmaker_id, publicsite_lawmaker.name, publicsite_lawmaker.crp_id, Count(publicsite_event_beneficiary.event_id) AS CountOfevent_id FROM publicsite_lawmaker INNER JOIN ((((publicsite_host INNER JOIN publicsite_crp_lobbying ON publicsite_host.crp_id = publicsite_crp_lobbying.datekey) INNER JOIN publicsite_event_hosts ON publicsite_host.id = publicsite_event_hosts.host_id) INNER JOIN publicsite_event ON publicsite_event_hosts.event_id = publicsite_event.id) INNER JOIN publicsite_event_beneficiary ON publicsite_event.id = publicsite_event_beneficiary.event_id) ON publicsite_lawmaker.id = publicsite_event_beneficiary.lawmaker_id WHERE (((publicsite_event.status) Is Null Or (publicsite_event.status)='') AND ((publicsite_crp_lobbying.realcode)='m1000')) GROUP BY publicsite_event_beneficiary.lawmaker_id, publicsite_lawmaker.name, publicsite_lawmaker.crp_id ORDER BY Count(publicsite_event_beneficiary.event_id) DESC LIMIT 12;"
    cursor.execute(query)
    polset = cursor.fetchall()

    """get list of committees sat on by party beneficiaries"""
    query = "SELECT publicsite_committee.title, Count(a.lawmaker_id) AS CountOflawmaker_id FROM publicsite_committee INNER JOIN ((SELECT publicsite_event_beneficiary.event_id, publicsite_event_beneficiary.lawmaker_id FROM (((publicsite_host INNER JOIN publicsite_crp_lobbying ON publicsite_host.crp_id = publicsite_crp_lobbying.datekey) INNER JOIN publicsite_event_hosts ON publicsite_host.id = publicsite_event_hosts.host_id) INNER JOIN publicsite_event ON publicsite_event_hosts.event_id = publicsite_event.id) INNER JOIN publicsite_event_beneficiary ON publicsite_event.id = publicsite_event_beneficiary.event_id WHERE (((publicsite_event.status) Is Null Or (publicsite_event.status)='') AND ((publicsite_crp_lobbying.realcode)='x3000'))) a INNER JOIN publicsite_committee_members ON a.lawmaker_id = publicsite_committee_members.lawmaker_id) ON publicsite_committee.short = publicsite_committee_members.committee_id GROUP BY publicsite_committee.title ORDER BY Count(a.lawmaker_id) DESC LIMIT 12;"
    cursor.execute(query)
    cmteset = cursor.fetchall()


    docset = Event.objects.filter(hosts__crp_lobbying__category=category, status='').order_by('-start_date')

    return render_to_response('publicsite/lobbydetail.html', {"snapshot_image_name":"recent", "docset":docset, "lobset": corps, "polset": polset, "cmteset": cmteset, "category": cat })


def lobbydetailcorp(request, name):
    #hostset = Host.objects.filter(crp_lobbying__category=category)
    lobset = Crp_lobbying.objects.filter(org=name)
    docset = Event.objects.filter(hosts__crp_lobbying__org=name, status='').order_by('-start_date')
    return render_to_response('publicsite/lobbydetailcorp.html', {"snapshot_image_name":"recent", "docset":docset, "lobset": lobset, "name": name })




def admin_uploadzip(request):    
    import os, zipfile, cStringIO
    from django.contrib.auth.decorators import login_required
    import datetime

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
                if zfname[-4:]=='.pdf':
                    newe = Event(status='temp')
                    newe.save()
                    pk = newe.pk
                    localfilename = 'flyer_'+str(pk)+'.pdf'
                    syspath = '/var/www/files.politicalpartytime.org/pdfs/'
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
                    newe.pdf_document_link = '/' + dirpath + localfilename
                    newe.save()
            return HttpResponseRedirect('/admin/publicsite/event/')
    else:
        return HttpResponseRedirect('/')




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

class PartyTimeLayar(LayarView):

    def get_partytime_queryset(self, latitude, longitude, radius, **kwargs):
        deg_in_m = 111045.0

        width = radius / math.fabs(math.cos(math.radians(latitude))*deg_in_m)
        height = (radius / deg_in_m)
        latitude_range = (str(latitude-height), str(latitude+height))
        longitude_range = (str(longitude-width), str(longitude+width))
        venues = Venue.objects.filter(latitude__range=latitude_range,
                                      longitude__range=longitude_range)
        return venues

    def poi_from_partytime_item(self, item):
        venue_url = 'http://politicalpartytime.org/search/Venue_Name/%s/' % item.venue_name
        actions = [{'label':venue_url}]
        return POI(id=item.id, lat=item.latitude, lon=item.longitude,
                   title=item.venue_name)

partytime_layar = PartyTimeLayar()
