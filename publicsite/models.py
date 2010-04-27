from django.db import models
from django.db import connection
import datetime
import re
from django.contrib import admin

#from publicsite.widgets import TimeWidget

from sunlightapi import sunlight, SunlightApiError
sunlight.apikey = '***REMOVED***'

BLOCK_ELEMENTS = ('blockquote','ol','ul')
BLOCK_ELEMENT_RE = re.compile(r"(%s)" % "|".join([r"<%s>(.*?)</%s>" % (e, e) for e in BLOCK_ELEMENTS]))

NONBLOCK_ELEMENTS = ('li',)
NONBLOCK_ELEMENT_RE = re.compile(r"(%s)" % "|".join([r">(\s*?)<(%s)" % e for e in NONBLOCK_ELEMENTS]),re.S)



class Crp_category(models.Model):
    realcode = models.CharField(max_length=5, primary_key=True)
    catname = models.CharField(blank=True, max_length=255,null=True) 
    sector = models.CharField(blank=True, max_length=255,null=True) 

class Crp_lobbying(models.Model):
    datekey = models.ForeignKey('Host', to_field='crp_id', primary_key=True, db_column='datekey')
    org = models.CharField(blank=True, max_length=255,null=True) 
    category = models.ForeignKey(Crp_category, to_field='realcode', db_column='realcode')




class Author(models.Model):
    user_name = models.CharField(max_length=255, db_column='display_name')

    class Meta:
        db_table = 'wp_users'
    
    def __unicode__(self):
        return self.user_name
        
    def save(self):
        pass
        
    def delete(self):
        pass
    
class Post(models.Model):
    title = models.CharField(max_length=255, db_column='post_title')
    content = models.TextField(db_column='post_content')
    post_date = models.DateTimeField('post date')
    guid = models.CharField(max_length=255)
    post_status = models.CharField(max_length=255)
    post_type = models.CharField(max_length=255)
    author = models.ForeignKey(Author, related_name='posts', db_column='post_author')
    comment_count = models.IntegerField()
    
    category_cache = None
    tag_cache = None
	
    class Meta:
    	db_table = 'wp_posts'
    	
    def __unicode__(self):
        return self.title
        
    def clean_content(self):
        content = BLOCK_ELEMENT_RE.sub(r"\n\1\n", self.content).strip()
       	content = NONBLOCK_ELEMENT_RE.sub(r"><\3",content)
       	return content
        
    def categories(self):
        if not self.category_cache:
            taxonomy = "category"
            self.category_cache = self._get_terms(taxonomy)
        return self.category_cache
        
    def tags(self):
        if not self.tag_cache:
            taxonomy = "post_tag"
            self.tag_cache = self._get_terms(taxonomy)
        return self.tag_cache
        
    def _get_terms(self, taxonomy):
        sql = """SELECT t.name, t.slug FROM wp_terms t INNER JOIN wp_term_taxonomy tt ON t.term_id = tt.term_id INNER JOIN wp_term_relationships tr ON tt.term_taxonomy_id = tr.term_taxonomy_id WHERE tt.taxonomy = %s AND tr.object_id = %s ORDER BY tr.term_order"""
        cursor = connection.cursor()
        cursor.execute(sql, [taxonomy, self.id])
        return [{'name': row[0], 'slug': row[1]} for row in cursor.fetchall()]
        
    def save(self):
        pass
        
    def delete(self):
        pass
        
class EventManager(models.Manager):
    def ical(self):
        events = Event.objects.filter(start_date__gt=datetime.datetime.now(),status='').order_by('start_date','start_time')[:50]
        return events 
   
    def recent(self, limit=10):
        events = Event.objects.filter(
                    start_date__lt=datetime.datetime.now(),
                    status='').order_by('-start_date','-start_time')[:limit]
        return events
        
    def upcoming(self, limit=10):
        events = Event.objects.filter(
                    start_date__gte=datetime.datetime.now(),
                    status='').order_by('start_date','start_time')[:limit]
        return events
        
    def daterange(self, start, end):
        startdate = datetime.datetime(int(start[0:4]),int(start[4:6]),int(start[6:8]))
        enddate = datetime.datetime(int(end[0:4]),int(end[4:6]),int(end[6:8]))
        events = Event.objects.filter(
                    start_date__gte=startdate, start_date__lte=enddate,
                    status='').order_by('start_date','start_time')
        return events


    def by_field(self, field, args, limit=10):
        try:
            events = Event.objects.filter(status='').order_by('-start_date','-start_time')
            if field == 'beneficiary':
                events = events.filter(beneficiaries__name__icontains=args)
            elif field == 'host':
                events = events.filter(hosts__name__icontains=args)
            elif field == 'other_members_of_congress':
                events = events.filter(other_members__name__icontains=args)
            elif field == 'venue_name':
                events = events.filter(venue__venue_name__icontains=args)
            elif field == 'entertainment_type':
                events = events.filter(entertainment__icontains=args)
            elif field == 'tags':
                events = events.filter(tags__tag_name__icontains=args)
            else:
                events = events.filter(**{str(field): str(args)})
            return events
        except:
            pass

	
    def by_cmte(self, cmteid):
        since_year = 2009 #beginning of election cycle
        cmte = Committee.objects.get(short=cmteid)
        ev = Event.objects.filter(status='', start_date__gte=datetime.datetime(since_year,1,1) ).filter(beneficiaries__committee = cmte).order_by('-start_date','-start_time').distinct()
        retu = {"cmte": cmte, "events": ev, "members": cmte.members.all(), "since_year": since_year } 
        return retu



class Host(models.Model):
    name = models.CharField(blank=True,max_length=255, db_index=True)
    crp_id = models.CharField(blank=True, max_length=18)
    #crp_id = models.ForeignKey(Crp_lobbying, to_field='datekey', db_column='crp_id')
    class Meta:
        db_table = u'publicsite_host'
    def __unicode__(self):
        return self.name
    def lobby(self):
        if self.crp_id==None:
            return None
        else:    
            return Crp_lobbying.objects.filter(datekey=self.crp_id)

    def natural_key(self):
        return (self.name)


class Tag(models.Model):
    tag_name = models.CharField(blank=True,max_length=255, db_index=True)
    class Meta:
        db_table = u'publicsite_tags'
    def __unicode__(self):
        return self.tag_name

class Lawmaker(models.Model):
    title = models.CharField("Title (Senator, Representative", blank=True,max_length=25)
    name = models.CharField(blank=True,max_length=255) #db_index=True
    first_name = models.CharField(blank=True,max_length=25)
    #middle_name = models.CharField(blank=True,max_length=25)
    last_name = models.CharField(blank=True,max_length=25)
    party = models.CharField(blank=True,max_length=1)
    state = models.CharField(blank=True,max_length=2)
    district = models.CharField(blank=True,max_length=2)
    crp_id =  models.CharField(blank=True,max_length=15)
    affiliate =  models.CharField("If this is a leadership PAC, this 'affiliate' field is the lawmaker's name", blank=True,max_length=200)

    class Meta:
        db_table = u'publicsite_lawmaker'
    def __unicode__(self):
        if self.district:
            districtStr ="-" +self.district	
        else:
            districtStr ="" 
        if self.party:
            partyStr =self.party+", "
        else:
            partyStr = ""
        if self.title:
            titleStr =self.title+" "
        else:
            titleStr = ""
        if self.district==None and self.party==None and self.state==None:
            info = ""
        else:
            info =" ("+partyStr+self.state+districtStr+")"
        return u"%s%s%s" % (titleStr, self.name,info) 

    def natural_key(self):
        return (self.name)

class Committee(models.Model):
    short = models.CharField(blank=False,max_length=4, primary_key=True)
    title = models.CharField(blank=False,max_length=100)
    members = models.ManyToManyField(Lawmaker)
    chamber = models.CharField(blank=False,max_length=10)
    def __unicode__(self):
        return self.title

class OtherInfo(models.Model):
    event_id = models.IntegerField(null=True, blank=True)
    lawmaker_id = models.IntegerField(null=True, blank=True)
    moc_type = models.IntegerField(null=True, blank=True)
    host_id = models.IntegerField(null=True, blank=True)
    other_info = models.TextField(blank=True)
    class Meta:
        db_table = u'publicsite_other_info'
    def __unicode__(self):
        return self.other_info

class Venue(models.Model):
    venue_name = models.CharField(blank=True,max_length=255)
    address1 = models.CharField(blank=True, max_length=70)
    address2 = models.CharField(blank=True, max_length=70)
    city = models.CharField(blank=True, max_length=50)
    state = models.CharField(blank=True, max_length=6)
    zipcode = models.CharField(blank=True, max_length=11)
    latitude = models.DecimalField(blank=True, null=True, max_digits=9, decimal_places=6, db_index=True)
    longitude = models.DecimalField(blank=True, null=True, max_digits=9, decimal_places=6)
    website = models.CharField(blank=True,max_length=255)
    def __unicode__(self):
        address = self.venue_address()
        if self.venue_name and address!='':
            return u"%s (%s)" % (self.venue_name, address)  
        elif self.venue_name:
            return self.venue_name
        else:
            return address
  
    def venue_address(self):    
        if self.address1 and self.address2:
            return u"%s %s" % (self.address1, self.address2)   
        elif self.address1 and self.city and self.city!='Washington':
            return u"%s, %s" % (self.address1, self.city) 
        elif self.address1:
            return self.address1
        elif self.city and self.state and self.state!='DC':
            return u"%s, %s" % (self.city, self.state) 
        else:
            return ""   

    def natural_key(self):
        return (self.venue_name)







class Event(models.Model):
    from django import forms
    import widgets

    objects = EventManager()

    entertainment = models.CharField(blank=True, max_length=205, null=True)    
    venue = models.ForeignKey(Venue,null=True,blank=True)

    hosts = models.ManyToManyField(Host,db_table=u'publicsite_event_hosts',null=True,blank=True, db_column='host_id')
    tags = models.ManyToManyField(Tag,db_table=u'publicsite_event_tags',null=True)
    beneficiaries = models.ManyToManyField(Lawmaker, null=True,blank=True, related_name='pol_events',db_table=u'publicsite_event_beneficiary')
    other_members = models.ManyToManyField(Lawmaker,null=True,blank=True, related_name='pol_appearances',db_table=u'publicsite_event_omc')
     
    start_date = models.DateField(blank=True, null=True)
    start_time = models.TimeField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)

    status = models.CharField(blank=True, max_length=255, db_index=True,null=True)    
    pdf_document_link = models.CharField(blank=True, max_length=255, help_text='<a onclick="tryPDF()">Load PDF</a>')

    committee_id = models.CharField(blank=True, max_length=255,null=True)    
    rsvp_info = models.CharField(null=True,blank=True, max_length=255)
    distribution_paid_for_by = models.CharField(blank=True, max_length=255,null=True)
    make_checks_payable_to = models.CharField(blank=True, max_length=255,null=True)
    checks_payable_to_address = models.CharField(blank=True, max_length=255,null=True)
    contributions_info = models.CharField(blank=True, max_length=255,null=True)
    user_initials = models.CharField(blank=True, max_length=5,null=True)
    data_entry_problems = models.CharField(blank=True, max_length=255,null=True)
 
        
    class Meta:
        db_table = u'publicsite_event'
    def __unicode__(self):
        if self.entertainment and self.venue:
            return self.entertainment + " at " + self.venue.venue_name
        elif self.venue:
            return self.venue.venue_name
        elif self.entertainment:
           return self.entertainment
        else:
            return "Event"    





    def sendemailalert(self):
        from django.template.loader import get_template
        from django.template import Context
        from django.core.mail import send_mail, EmailMultiAlternatives
        import datetime
        if (self.status=='' or self.status==None): 
            states = []    
            bens = ''       
            hosts = ''
            for h in self.hosts.all():
                if hosts=='':
                    hosts = h.name
                else:
                    hosts = hosts + ', ' + h.name
            for b in self.beneficiaries.all():
                bens = bens + b.name + ", "
                if b.state and b.state!='':
                    if b.state not in states:
                        states.append(b.state)
                elif b.crp_id and b.affiliate:
                    l = Lawmaker.objects.find(crp_id=b.crp_id, affiliate__isnull=True)
                    for ll in l:
                        if ll.state not in states and ll.state!='':
                            states.append(ll.state)                    
            for state in states:
                emaillist = StateMailingList.objects.filter(state=state, confirmed=True)
                for l in emaillist:    
                    subject = "PoliticalPartyTime: " + bens[:-2] + " fundraiser " + self.start_date.strftime("%Y-%m-%d")
                    if hosts!='':
                        subject = subject + " hosted by " + hosts
                    t = get_template('feeds/party_description.html')
                    html = t.render(Context({'obj': self}))
                    body = '<p><a href="http://politicalpartytime.org/party/' + str(self.pk) + '">Click here to view invitation on the Sunlight Foundation\'s PoliticalPartytime.org.</a></p>'+ html + '<p>To unsubscribe from these alerts, <a href="http://politicalpartytime.org/emailalerts/?email='+l.email+'&state='+l.state+'&remove='+str(l.confirmation)+'">click here</a>.</p>'
                    email = EmailMultiAlternatives(subject, body, 'bounce@politicalpartytime.org', [l.email])
                    email.attach_alternative(body, "text/html")
                    email.send()

from django.dispatch import dispatcher
from django.db.models import signals

def change_watcher(sender, instance, raw, signal, created, **kwargs):
    instance.sendemailalert()

signals.post_save.connect(change_watcher, sender=Event)

class StateMailingList(models.Model):

    email = models.EmailField()
    confirmation = models.IntegerField(max_length=36)
    confirmed = models.BooleanField(default=False)
    state = models.CharField(max_length=2)

    def __unicode__(self):
        return self.state + ": " + self.email


