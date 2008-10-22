from django.db import models
from django.db import connection
import datetime
import re

BLOCK_ELEMENTS = ('blockquote','ol','ul')
BLOCK_ELEMENT_RE = re.compile(r"(%s)" % "|".join([r"<%s>(.*?)</%s>" % (e, e) for e in BLOCK_ELEMENTS]))

NONBLOCK_ELEMENTS = ('li',)
NONBLOCK_ELEMENT_RE = re.compile(r"(%s)" % "|".join([r">(\s*?)<(%s)" % e for e in NONBLOCK_ELEMENTS]),re.S)

class Author(models.Model):
    user_name = models.CharField(max_length=255, db_column='user_nicename')

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
                events = events.filter(entertainment__entertainment_type__icontains=args)
            elif field == 'tags':
                events = events.filter(tags__tag_name__icontains=args)
            else:
                events = events.filter(**{str(field): str(args)})
            return events
        except:
            pass

class Host(models.Model):
    name = models.CharField(blank=True,max_length=255, db_index=True)
    class Meta:
        db_table = u'publicsite_host'
    def __unicode__(self):
        return self.name

class Tag(models.Model):
    tag_name = models.CharField(blank=True,max_length=255, db_index=True)
    class Meta:
        db_table = u'publicsite_tags'
    def __unicode__(self):
        return self.tag_name

class Lawmaker(models.Model):
    title = models.CharField(blank=True,max_length=25)
    name = models.CharField(blank=True,max_length=255, db_index=True)
    party = models.CharField(blank=True,max_length=1)
    state = models.CharField(blank=True,max_length=2)
    district = models.CharField(blank=True,max_length=2)
    class Meta:
        db_table = u'publicsite_lawmaker'
    def __unicode__(self):
	if self.district=="":
	    districtStr = ""
	else:
	    districtStr ="-"+self.district
	
        if self.party=="":
	    partyStr = ""
	else:
	    partyStr =self.party+", "

        if self.title=="":
	    titleStr = ""
	else:
	    titleStr =self.title+" "

	if self.district=="" and self.party=="" and self.state=="":
	    info = ""
	else:
	    info ="("+partyStr+self.state+districtStr+")"
	
	#districtStr = "" if self.district=="" else "-"+self.district
	#partyStr = "" if self.party=="" else self.party+", "
	#info =  "" if self.district=="" and self.party=="" and self.state=="" else " ("+partyStr+self.state+districtStr+")"
        return u"%s%s%s" % (titleStr, self.name,info) 

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
    venue_address = models.TextField(blank=True)
    latitude = models.DecimalField(blank=True, null=True, max_digits=9, decimal_places=6, db_index=True)
    longitude = models.DecimalField(blank=True, null=True, max_digits=9, decimal_places=6)
    def __unicode__(self):
        return self.venue_name

class Entertainment(models.Model):
    entertainment_type = models.CharField(max_length=255)
    class Meta:
        db_table = u'publicsite_entertainment'
    def __unicode__(self):
        return self.entertainment_type

class Event(models.Model):
    objects = EventManager()

    entertainment = models.ForeignKey(Entertainment,null=True)
    venue = models.ForeignKey(Venue,null=True)

    hosts = models.ManyToManyField(Host,db_table=u'publicsite_event_hosts')
    tags = models.ManyToManyField(Tag,db_table=u'publicsite_event_tags')
    beneficiaries = models.ManyToManyField(Lawmaker,db_table=u'publicsite_event_beneficiary', related_name='publicsite_event_beneficiary')
    other_members = models.ManyToManyField(Lawmaker,db_table=u'publicsite_event_omc', related_name='publicsite_event_omc')
     
    start_date = models.DateField(blank=True, null=True)
    start_time = models.TimeField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)

    status = models.CharField(blank=True, max_length=255, db_index=True)    
    pdf_document_link = models.CharField(blank=True, max_length=255)
    committee_id = models.CharField(blank=True, max_length=255)    
    rsvp_info = models.CharField(blank=True, max_length=255)
    event_paid_for_by = models.CharField(blank=True, max_length=255)
    distribution_paid_for_by = models.CharField(blank=True, max_length=255)
    make_checks_payable_to = models.CharField(blank=True, max_length=255)
    checks_payable_to_address = models.CharField(blank=True, max_length=255)
    contributions_info = models.CharField(blank=True, max_length=255)
    user_initials = models.CharField(blank=True, max_length=32)
    data_entry_problems = models.TextField(blank=True)
 
        
    class Meta:
        db_table = u'publicsite_event'
    def __unicode__(self):
        return u"%s at %s" % (self.entertainment.entertainment_type, self.venue.venue_name)
'''
class EventBeneficiary(models.Model):
    event_id = models.IntegerField(null=True, blank=True)
    lawmaker_id = models.IntegerField(null=True, blank=True)
    class Meta:
        db_table = u'publicsite_event_beneficiary'

class EventHosts(models.Model):
    event_id = models.IntegerField(primary_key=True)
    host_id = models.IntegerField()
    class Meta:
        db_table = u'publicsite_event_hosts'

class EventOmc(models.Model):
    event_id = models.IntegerField(primary_key=True)
    lawmaker_id = models.IntegerField()
    class Meta:
        db_table = u'publicsite_event_omc'

class EventTags(models.Model):
    tag_id = models.IntegerField(primary_key=True)
    event_id = models.IntegerField()
    class Meta:
        db_table = u'publicsite_event_tags'
'''



'''           
class Event(models.Model):
    
    objects = EventManager()
    
    status = models.CharField(blank=True, max_length=255, db_index=True)
    venue_id = 
    entertainment_id = 
     
    start_date = models.DateField(blank=True, null=True)
    start_time = models.TimeField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)
    
    pdf_document_link = models.CharField(blank=True, max_length=255)
    committee_id = models.CharField(blank=True, max_length=255)
    
    rsvp_info = models.CharField(blank=True, max_length=255)
    event_paid_for_by = models.CharField(blank=True, max_length=255)
    distribution_paid_for_by = models.CharField(blank=True, max_length=255)
    make_checks_payable_to = models.CharField(blank=True, max_length=255)
    checks_payable_to_address = models.CharField(blank=True, max_length=255)
    contributions_info = models.CharField(blank=True, max_length=255)
        
    user_initials = models.CharField(blank=True, max_length=32)
    data_entry_problems = models.TextField(blank=True)
    
    def __unicode__(self):
        return u"%s at %s" % (self.entertainment_type, self.venue_name)

class Other_Info(models.Model):
    tag_name = models.CharField(blank=True,max_length=255, db_index=True)
    
    def __unicode__(self):
        return self.tag_name

    
class Tags(models.Model):
    tag_name = models.CharField(blank=True,max_length=255, db_index=True)
    
    def __unicode__(self):
        return self.tag_name

class Host(models.Model):
    name = models.CharField(blank=True,max_length=255, db_index=True)
    event = models.ForeignKey(Event, related_name='hosts')
    
    def __unicode__(self):
        return self.name
    
class Lawmaker(models.Model):
    title = models.CharField(blank=True,max_length=25, db_index=True)
    name = models.CharField(blank=True,max_length=255, db_index=True)
    party = models.CharField(blank=True,max_length=1)
    state = models.CharField(blank=True,max_length=2)
    district = models.CharField(blank=True,max_length=2)

    event = models.ForeignKey(Event, related_name='other_members')
    
    def __unicode__(self):
        return self.name

class Venue(models.Model):
    venue_name = models.CharField(blank=True,max_length=255)
    venue_address = models.TextField(blank=True)
    latitude = models.DecimalField(blank=True, null=True, max_digits=9, decimal_places=6, db_index=True)
    longitude = models.DecimalField(blank=True, null=True, max_digits=9, decimal_places=6)
    def __unicode__(self):
        return self.venue_name

class Entertainment(models.Model):
    entertainment_type = models.CharField(blank=True, max_length=255)
    def __unicode__(self):
        return self.entertainment_type
'''