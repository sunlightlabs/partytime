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
from layar import LayarView, POI


def index(request):
    term = None
    now = datetime.datetime.now()

    if request.method == "POST":
        term = request.POST.get('term', None)

    if request.method == "GET":
        term = request.GET.get('term', None)

    if term:        
        blog_posts = Post.objects.filter(post_type='post', post_status='publish', content__icontains=term).order_by('-post_date')[:10]
    else:
        blog_posts = Post.objects.filter(post_type='post', post_status='publish').order_by('-post_date')[:10]

    return render_to_response(
            'publicsite/index.html', 
            {'blog_posts': blog_posts, }, 
            context_instance = RequestContext(request)
            )


def party(request, docid): 
    doc = get_object_or_404(Event, pk=docid)
    return render_to_response('publicsite/party.html', {"doc": doc}) 


def search_proxy(request):
    field = request.REQUEST.get('field', None)
    args = request.REQUEST.get('args', None)

    if field and args:
        redirect_url = '/search/%s/%s/' % (field, args)
        return HttpResponseRedirect(redirect_url)

    return HttpResponseRedirect('/')


def search(request, field, args):
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


#
# upcoming and recent events
#

def recent(request):
    docset = Event.objects.recent(15)
    return render_to_response(
            'publicsite/snapshot.html', 
            {'snapshot_image_name': 'recent', 
             'docset': docset, }
            )


def upcoming(request):
    docset = Event.objects.upcoming(None)
    paginator = Paginator(docset, 25, orphans=5)
    pagenum = request.GET.get('page', 1)
    try:
        page = paginator.page(pagenum)
    except (EmptyPage, InvalidPate):
        raise Http404

    return render_to_response(
            'publicsite/snapshot.html',
            {'snapshot_image_name': 'upcoming', 
             'page': page,
             }
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
    return render_to_response(
                'publicsite/snapshot.html', 
                {'snapshot_image_name': '', 
                 'docset':docset, }
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

    return render_to_response(
            'publicsite/snapshot.html', 
            {'snapshot_image_name': '', 'docset': docset, }
            )


def leadpacs(request):
    docset = Event.objects.filter(status='', beneficiaries__affiliate__isnull=False) \
                          .order_by('-start_date', '-start_time')[0:6]

    return render_to_response(
            'publicsite/leadpacs.html', 
            {'docset': docset, })


def polwithpac(request, cid):
    lm = None
    pacname = None
    polname = None

    l = Lawmaker.objects.filter(crp_id=cid) \
                        .distinct()

    if l.count() == 0:
        return HttpResponseRedirect('/')     

    for ll in l:
        if ll.affiliate:
            pacname = ll.name
        else:
            lm = ll
      
    eventlist = Event.objects.filter(status='', beneficiaries__crp_id=cid) \
                             .order_by('-start_date', '-start_time')

    return render_to_response(
            'publicsite/polwithpac.html',
            {'eventlist': eventlist,
             'lm': lm,
             'pacname': pacname,
             'snapshot_image_name': '', }
            )


#
# file uploading
#

def upload(request):
    if request.method == 'POST' and request.FILES:
        uf = request.FILES.get('pdf', None)

        if uf:
            if uf.name.endswith(".pdf") and uf.size < 1024 * 1024 * 100:  # size < 100MB
                path = "%s/upload/%s.pdf" % (settings.FILE_UPLOAD_PATH, random.randint(100000,999999))
                destination = open(path, 'wb')

                for chunk in uf.chunks():
                    destination.write(chunk)
                    return HttpResponseRedirect('/upload/thanks/')

    return render_to_response(
            'publicsite/upload.html', 
            context_instance = RequestContext(request)
            )
    

def upload_thanks(request):
    return HttpResponse("thanks")


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


@cache_page(60*30)
def committee_leadership(request):
    """Turning the querysets into lists to avoid subqueries.
    """
    crp_ids = list(CommitteeMembership.objects.values_list('member__crp_id', flat=True).exclude(position='Member'))
    leadership_ids = list(Lawmaker.objects.filter(crp_id__in=crp_ids).values_list('id', flat=True))

    events = Event.objects.filter(Q(beneficiaries__in=leadership_ids) | Q(other_members__in=leadership_ids)
                        ).distinct().order_by('-start_date', 'start_time')

    paginator = Paginator(events, 50, orphans=5)
    pagenum = request.GET.get('page', 1)

    try:
        page = paginator.page(pagenum)
    except (EmptyPage, InvalidPage):
        raise Http404

    return render_to_response(
            'publicsite/leadership.html',
            {'page': page,
             'title': 'Events held for or attended by committee leaders',
             'pagetype': 'committee',
            },
        )


@cache_page(60*30)
def congressional_leadership(request):
    """Turning the querysets into lists to avoid subqueries.
    """
    crp_ids = list(LeadershipPosition.objects.values_list('lawmaker__crp_id', flat=True))
    leadership_ids = list(Lawmaker.objects.filter(crp_id__in=crp_ids).values_list('id', flat=True))


    events = Event.objects.filter(Q(beneficiaries__in=leadership_ids) | Q(other_members__in=leadership_ids)
                        ).distinct().order_by('-start_date', 'start_time')

    paginator = Paginator(events, 50, orphans=5)
    pagenum = request.GET.get('page', 1)

    try:
        page = paginator.page(pagenum)
    except (EmptyPage, InvalidPage):
        raise Http404

    return render_to_response(
            'publicsite/leadership.html',
            {'page': page,
             'title': 'Events held for or attended by congressional leaders',
             'pagetype': 'congressional',
            },
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

    watermarker = WatermarkAdder('/var/www/files.politicalpartytime.org/pdfs/partytimesource.pdf')

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
                newe = Event(status='temp', scribd_id=0)
                newe.save()
                pk = newe.pk
                localfilename = 'flyer_'+str(pk)+'_original.pdf'
                watermarked_pdf_filename = 'flyer_%s.pdf' % str(pk)
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

