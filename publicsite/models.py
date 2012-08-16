from collections import defaultdict
import datetime
import re

from django.contrib import admin
from django.contrib.sites.models import Site
from django.core.mail import send_mail, EmailMultiAlternatives
from django.db import connection
from django.db import models
from django.db.models import Q
from django.template import Context
from django.template.loader import get_template

from django.contrib.localflavor.us.us_states import US_STATES

import scribd
import postmark

from settings import SCRIBD_KEY, SCRIBD_SECRET

from sunlightapi import sunlight, SunlightApiError
sunlight.apikey = '***REMOVED***'

state_dict = dict(US_STATES)

BLOCK_ELEMENTS = ('blockquote', 'ol', 'ul')
BLOCK_ELEMENT_RE = re.compile(r'(%s)' % '|'.join([r'<%s>(.*?)</%s>' % (e, e) for e in BLOCK_ELEMENTS]))

NONBLOCK_ELEMENTS = ('li',)
NONBLOCK_ELEMENT_RE = re.compile(r'(%s)' % '|'.join([r'>(\s*?)<(%s)' % e for e in NONBLOCK_ELEMENTS]),re.S)


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


# class Post(models.Model):
#     title = models.CharField(max_length=255, db_column='post_title')
#     content = models.TextField(db_column='post_content')
#     post_date = models.DateTimeField('post date')
#     guid = models.CharField(max_length=255)
#     post_status = models.CharField(max_length=255)
#     post_type = models.CharField(max_length=255)
#     author = models.ForeignKey(Author, related_name='posts', db_column='post_author')
#     comment_count = models.IntegerField()
# 
#     category_cache = None
#     tag_cache = None
# 
#     class Meta:
#       db_table = 'wp_posts'
# 
#     def __unicode__(self):
#         return self.title
# 
#     def clean_content(self):
#         content = BLOCK_ELEMENT_RE.sub(r"\n\1\n", self.content).strip()
#           content = NONBLOCK_ELEMENT_RE.sub(r"><\3",content)
#           return content
# 
#     def categories(self):
#         if not self.category_cache:
#             taxonomy = "category"
#             self.category_cache = self._get_terms(taxonomy)
#         return self.category_cache
# 
#     def tags(self):
#         if not self.tag_cache:
#             taxonomy = "post_tag"
#             self.tag_cache = self._get_terms(taxonomy)
#         return self.tag_cache
# 
#     def _get_terms(self, taxonomy):
#         sql = """SELECT t.name,
#                         t.slug
#                     FROM wp_terms t
#                     INNER JOIN wp_term_taxonomy tt
#                         ON t.term_id = tt.term_id
#                     INNER JOIN wp_term_relationships tr
#                         ON tt.term_taxonomy_id = tr.term_taxonomy_id
#                     WHERE tt.taxonomy = %s
#                         AND
#                           tr.object_id = %s
#                   ORDER BY tr.term_order"""
#         cursor = connection.cursor()
#         cursor.execute(sql, [taxonomy, self.id])
#         return [{'name': row[0], 'slug': row[1]} for row in cursor.fetchall()]
# 
#     def save(self):
#         pass
# 
#     def delete(self):
#         pass


class EventManager(models.Manager):

    def ical(self):
        events = Event.objects.filter(start_date__gt=datetime.datetime.now(),status='') \
                               .order_by('start_date', 'start_time')[:50]
        return events

    def recent(self, limit=10):
        events = Event.objects.filter(
                    start_date__lt=datetime.datetime.now(),
                    status='').order_by('-start_date', '-start_time')[:limit]
        return events

    def upcoming(self, limit=10):
        events = Event.objects.filter(
                    start_date__gte=datetime.date.today(),
                    status='').order_by('start_date', 'start_time')
        if limit:
            events = events[:limit]
        return events

    def presidential(self, limit=10):
        events = Event.objects.filter(
                    start_date__lt=datetime.datetime.now(),
                    status='', is_presidential=True).order_by('-start_date', '-start_time')[:limit]
        return events

    # this isn't, strictly speaking, the newest; it's the newest parties that haven't already happened. 
    def newest(self, limit=10):
        events = Event.objects.filter(
                    start_date__gte=datetime.date.today(),
                    status='').order_by('-added')
        if limit:
            events = events[:limit]
        return events

    # Why does it expect dates in %Y%m%d format instead of as datetime.date objects? No idea. -jf
    def daterange(self, start, end):
        startdate = datetime.datetime(int(start[0:4]), int(start[4:6]), int(start[6:8]))
        enddate = datetime.datetime(int(end[0:4]), int(end[4:6]), int(end[6:8]))
        events = Event.objects.filter(
                    start_date__gte=startdate, start_date__lte=enddate,
                    status='').order_by('start_date', 'start_time')
        return events

    def month(self, year, month):
        startdate = datetime.date(year, month, 1)
        enddate = datetime.date(year, month+1, 1)
        events = Event.objects.filter(
                    start_date__gte=startdate, start_date__lt=enddate,
                    status='').order_by('start_date', 'start_time')
        return events

    def by_field(self, field, args, limit=10):
        try:
            events = Event.objects.filter(status='').order_by('-start_date','-start_time')
            if field == 'beneficiary':
                events = events.filter(beneficiaries__name__icontains=args) | events.filter(beneficiaries__affiliate__icontains=args)
            elif field == 'host':
                events = events.filter(hosts__name__icontains=args)
            elif field == 'other_members_of_congress':
                events = events.filter(other_members__name__icontains=args)
            elif field == 'venue_name':
                events = events.filter(venue__venue_name__icontains=args)
            elif field == 'entertainment_type':
                events = events.filter(entertainment__icontains=args)
            elif field == 'city':
                (city, state) = args.split('-')
                events = events.filter(venue__city__icontains=args, venue__state=state)    
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
        ev = Event.objects.filter(status='',
                                  start_date__gte=datetime.datetime(since_year, 1, 1),
                                  beneficiaries__committee__short = cmteid
                                 ).order_by('-start_date','-start_time').distinct()
        return {'cmte': cmte, 'events': ev, 'members': cmte.members.all(), 'since_year': since_year}


class Host(models.Model):
    name = models.CharField(blank=True, max_length=255, db_index=True)
    crp_id = models.CharField(u'CRP ID', blank=True, max_length=18)

    class Meta:
        db_table = u'publicsite_host'

    def __unicode__(self):
        return self.name

    def natural_key(self):
        return (self.name)


class Tag(models.Model):
    tag_name = models.CharField(blank=True,max_length=255, db_index=True)

    class Meta:
        db_table = u'publicsite_tags'

    def __unicode__(self):
        return self.tag_name


class Lawmaker(models.Model):
    title = models.CharField(help_text=u'(e.g., Senator, Representative)', blank=True,max_length=25)
    name = models.CharField(blank=True, max_length=255)
    party = models.CharField(blank=True, max_length=1)
    state = models.CharField(blank=True, max_length=2)
    district = models.CharField(blank=True, max_length=2)
    crp_id =  models.CharField(u'CRP ID', blank=True, max_length=15)
    affiliate =  models.CharField(help_text=u"If this is a leadership PAC, this field is the lawmaker's name", blank=True,max_length=200)

    class Meta:
        db_table = u'publicsite_lawmaker'

    def __unicode__(self):
        if self.district:
            district_str = '-%s' % self.district
        else:
            district_str = ''

        if self.party:
            party_str = '%s, ' % self.party
        else:
            party_str = ''

        if self.title:
            title_str = '%s ' % self.title
        else:
            title_str = ''

        if not self.district and not self.party and not self.state:
            info = ''
        else:
            info = ' (%s%s%s)' % (party_str, self.state, district_str)

        return u'%s%s%s' % (title_str, self.name, info)
             

    def natural_key(self):
        return (self.name)
        
    def titled_name(self):
        if self.title:
            title_str = '%s ' % self.title
        else:
            title_str = ''
        return u'%s%s' % (title_str, self.name)        

    def events_since_year(self, year=2009):
        return self.pol_events.filter(start_date__gte=datetime.date(year, 01, 01))

    def committee_position(self, committee):
        """Get this lawmaker's position on the given committee.

        Returns None if the lawmaker isn't on the given committee.
        """
        try:
            return CommitteeMembership.objects.get(committee=committee, member=self).position
        except CommitteeMembership.DoesNotExist:
            return None

    def committee_leadership_positions(self):
        return self.committeemembership_set.filter(Q(position='Chair') |
                                                   Q(position='Vice Chair') |
                                                   Q(position='Ranking Member'))

    def congressional_leadership_positions(self):
        return self.leadershipposition_set.all()


    def all_leadership_positions(self):
        positions = []
        for position in self.committee_leadership_positions():
            positions.append('%s, %s' % (position.position, position.committee.title))

        for position in self.congressional_leadership_positions():
            positions.append(position.position)

        return positions

    def affiliate_leadership_positions(self):
        positions = []
        lawmaker = Lawmaker.objects.filter((Q(affiliate='') | Q(affiliate=None)), crp_id=self.crp_id)
        if not lawmaker:
            return positions
        lawmaker = lawmaker[0]
        return lawmaker.all_leadership_positions()


class SuperCommitteeMember(models.Model):
    lawmaker = models.ForeignKey(Lawmaker)

    def __unicode__(self):
        return self.lawmaker.__unicode__()

class LeadershipPosition(models.Model):
    congress = models.CharField(u'Number of this congress (e.g. 111th',
                                max_length=8)
    lawmaker = models.ForeignKey(Lawmaker)
    position = models.CharField(u'The leadership position',
                                max_length=100)
    body = models.CharField(u'House or Senate',
                            max_length=1,
                            choices=(('H', 'House'),
                                     ('S', 'Senate'), )
                            )

    def __unicode__(self):
        return self.position


class Committee(models.Model):
    short = models.CharField(blank=False, max_length=4, primary_key=True)
    title = models.CharField(blank=False, max_length=100)
    members = models.ManyToManyField(Lawmaker, through='CommitteeMembership')
    chamber = models.CharField(blank=False, max_length=10)

    def __unicode__(self):
        return self.title

    @models.permalink
    def get_absolute_url(self):
        return ('partytime_committee_detail', [str(self.short), ])

    def events(self):
        return Event.objects.filter(
                            beneficiaries__in = self.members.all(),
                            start_date__gte = datetime.date(2009, 01, 01)
                        ).distinct()

    def chairman(self):
        try:
            return self.committeemembership_set.get(position='Chair').member
        except CommitteeMembership.DoesNotExist:
            return None

    def vice_chairman(self):
        try:
            return self.committeemembership_set.get(position='Vice Chair').member
        except CommitteeMembership.DoesNotExist:
            return None

    def ranking_members(self):
        # In joint committees, there are two ranking members.
        #
        # Sometimes listed as 'Ranking Member' and
        # sometimes 'Ranking Minority Member'
        return [x.member for x in self.committeemembership_set.filter(position__icontains='ranking')]

    def leadership_members(self):
        return self.committeemembership_set.filter(Q(position='Chair') |
                                                   Q(position='Vice Chair') |
                                                   Q(position='Ranking Member'))

    def non_leadership_members(self):
        return self.committeemembership_set.filter(position='Member')



class CommitteeMembership(models.Model):
    committee = models.ForeignKey(Committee)
    member = models.ForeignKey(Lawmaker)
    position = models.CharField(max_length=24)
    as_of = models.DateField(auto_now=True)


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

    townhouse = models.BooleanField(default=False)

    def __unicode__(self):
        address = self.venue_address()

        if self.venue_name and address is not None:
            return u'%s (%s)' % (self.venue_name, address)
        elif self.venue_name:
            return self.venue_name
        else:
            return address

    def venue_address(self):
        if self.address1 and self.address2:
            return u'%s %s' % (self.address1, self.address2)
        elif self.address1 and self.city and self.city != 'Washington':
            return u'%s, %s' % (self.address1, self.city)
        elif self.address1:
            return self.address1
        elif self.city and self.state and self.state != 'DC':
            return u'%s, %s' % (self.city, self.state)
        else:
            return ''

    def natural_key(self):
        return (self.venue_name)

    def political_parties(self):
        """How many events have been held for members of each
        political party at this venue.
        """
        parties = [lawmaker.party for sublist in [event.beneficiaries.all() for event in self.event_set.all()] for lawmaker in sublist]
        r = parties.count('R')
        d = parties.count('D')
        return {'Republican': r, 'Democrat': d, 'Parties': parties, }
        
    def state_full(self):
        try:
            return state_dict[self.state]
        except:
            return self.state

class Event(models.Model):
    from django import forms
    import widgets

    objects = EventManager()

    entertainment = models.CharField(blank=True, max_length=205, null=True)
    venue = models.ForeignKey(Venue, null=True, blank=True)

    hosts = models.ManyToManyField(Host, db_table=u'publicsite_event_hosts', null=True, blank=True, db_column='host_id')
    tags = models.ManyToManyField(Tag, db_table=u'publicsite_event_tags', null=True)
    beneficiaries = models.ManyToManyField(Lawmaker, null=True, blank=True, related_name='pol_events', db_table=u'publicsite_event_beneficiary')
    other_members = models.ManyToManyField(Lawmaker, null=True,blank=True, related_name='pol_appearances', db_table=u'publicsite_event_omc')

    start_date = models.DateField(blank=True, null=True)
    start_time = models.TimeField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)

    status = models.CharField(blank=True, max_length=255, db_index=True, null=True)
    pdf_document_link = models.CharField(blank=True, max_length=255, help_text='<a onclick="tryPDF()">Load PDF</a>')

    committee_id = models.CharField(blank=True, max_length=255,null=True)
    rsvp_info = models.CharField(u'RSVP info', null=True,blank=True, max_length=255)
    distribution_paid_for_by = models.CharField(blank=True, max_length=255, null=True)
    make_checks_payable_to = models.CharField(blank=True, max_length=255, null=True)
    checks_payable_to_address = models.CharField(blank=True, max_length=255, null=True)
    contributions_info = models.CharField(blank=True, max_length=255, null=True)
    user_initials = models.CharField(blank=True, max_length=5, null=True)
    data_entry_problems = models.CharField(blank=True, max_length=255, null=True)
    notes = models.TextField(blank=True)

    is_presidential = models.BooleanField(blank=True, default=False)

    canceled = models.BooleanField(u'This event has been canceled',
                                   blank=True,
                                   default=False)
    postponed = models.BooleanField(u'This event has been postponed',
                                    blank=True,
                                    default=False)

    scribd_upload = models.BooleanField(u'Upload PDF to Scribd',
                                        blank=True,
                                        default=True)
    scribd_id = models.IntegerField()
    scribd_url = models.URLField(u'Scribd URL', verify_exists=False, blank=True)

    added = models.DateTimeField(u'The date and time this event was added', auto_now_add=True)

    class Meta:
        db_table = u'publicsite_event'

    def __unicode__(self):
        if self.entertainment and self.venue:
            return '%s at %s' % (self.entertainment, self.venue.venue_name)
        elif self.venue:
            return self.venue.venue_name
        elif self.entertainment:
           return self.entertainment
        else:
            return 'Event'
            
    def truncated_name(self):
        name = self.__unicode__()
        #print name
        if len(name)> 21:
            return name[:21] + "..."
        else:
            return name


    def save(self):
        if self.scribd_upload and not self.status:
            self.upload_to_scribd()
        elif self.scribd_upload is not True and self.scribd_id:
            self.delete_from_scribd()

        super(Event, self).save()

    @models.permalink
    def get_absolute_url(self):
        return ('partytime_party_detail', [str(self.id), ])

    def event_title(self):
        title = ''
        if len(self.entertainment) > 2:
            title += self.entertainment
        else:
            title += 'Fundraiser'
        if self.beneficiaries.all():
            title += ' for %s ' % ', '.join([x.name for x in self.beneficiaries.all()])
        return title


    def upload_to_scribd(self):
        """Upload an event PDF to Scribd.
        """
        scribd.config(SCRIBD_KEY, SCRIBD_SECRET)

        pdf_url = 'http://files.politicalpartytime.org/pdfs%s' % self.pdf_document_link

        # If this invitation has already been uploaded
        # to Scribd, update it rather than uploading again.
        if self.scribd_id:
            doc = scribd.api_user.get(self.scribd_id)
        else:
            doc = scribd.api_user.upload_from_url(pdf_url,
                                                  access='private')

        event_url = 'http://%s%s' % (Site.objects.get_current().domain,
                                     self.get_absolute_url())

        if self.start_date:
            description = ("This is an invitation for a political fundraiser on %s. "
                           "Get details at Sunlight Foundation's "
                           "<a href=\"%s\">Party Time</a>"
                           ) % (self.start_date.strftime('%B %d, %Y'), event_url)
        else:
            description = ("This is an invitation for a political fundraiser. "
                           "Get details at Sunlight Foundation's "
                           "<a href=\"%s\">Party Time</a>"
                           ) % (event_url)

        params = {'title': self.event_title(),
                  'publisher': "Sunlight Foundation's Party Time",
                  'description': description,
                  'link_back_url': event_url,
                  'tags': self.make_scribd_tags(),
                  'category': 'Government Docs',
                  'access': 'public',
                  }

        scribd.update([doc,], **params)

        collections = scribd.api_user.get_collections()
        collection = [x for x in collections if x.collection_name == 'Party Time']
        if collection:
            collection = collection[0]
            try:
                doc.add_to_collection(collection)
            except:
                pass

        self.scribd_id = doc.id
        self.scribd_url = doc.get_scribd_url()

        return doc


    def delete_from_scribd(self):
        """Remove a PDF from scribd.
        """

        if not self.scribd_id:
            return False

        scribd.config(SCRIBD_KEY, SCRIBD_SECRET)

        try:
            doc = scribd.api_user.get(self.scribd_id)
        except scribd.ResponseError:
            self.scribd_id = 0
            self.scribd = False
            self.scribd_url = ''
            return False

        doc.delete()

        self.scribd_id = 0
        self.upload_to_scribd = False
        self.scribd_url = ''


    def make_scribd_tags(self):
        """Generate a list of tags for Scribd for
        the given event.

        The Scribd API requires the tag list to be
        in CSV format and does not allow quoting,
        so we remove any commas that may be part of tags.

        The tag list generated here is made up of the
        names of the hosts, beneficiaries, and other
        members for the event.
        """
        tags = []

        hosts = self.hosts.all()
        if hosts:
            tags += [host.name.replace(',', '') for host in hosts]

        beneficiaries = self.beneficiaries.all()
        if beneficiaries:
            tags += [beneficiary.name.replace(',', '')
                    for beneficiary in beneficiaries]

        others = self.other_members.all()
        if others:
            tags += [member.name.replace(',', '') for member in others]

        tags += ['politics', 'campaign', 'invitation', 'party', ]

        return ','.join(sorted(tags))


    def send_state_email(self):
        if self.status:
            return

        if self.start_date and self.start_date < datetime.date.today():
            return

        for beneficiary in self.beneficiaries.exclude(Q(state__isnull=True) | Q(state='')):
            subject = 'PoliticalPartyTime: Fundraiser for %s on %s' % (unicode(beneficiary),
                                                                       self.start_date.strftime('%B %d, %Y'))
            template = 'emails/state_email.html'
            state = beneficiary.state
            try:
                mailing_list = MailingList.objects.get(name=state)
            except MailingList.DoesNotExist: # Should never happen, but just in case.
                continue

            for subscriber in mailing_list.email_set.filter(mailinglistmembership__confirmed=True):
                membership = subscriber.mailinglistmembership_set.get(mailing_list=mailing_list)
                context = {'obj': self,
                           'email': subscriber.email,
                           'confirmation': membership.confirmation,
                           'list_id': mailing_list.id,
                           'cancellation_url': membership.cancellation_url(),
                           'subject': subject, }
                send_email(template, context)


def send_email(template, context):
    template = get_template(template)
    body = template.render(Context(context))
    email = EmailMultiAlternatives(context['subject'],
                                   body,
                                   'Party Time <partytime@sunlightfoundation.com>',
                                   [context['email'], ])
    email.attach_alternative(body, 'text/html')
    try:
        email.send()
    except postmark.PMMailUnprocessableEntityException:
        return


def change_watcher(sender, **kwargs):
    kwargs['instance'].send_state_email()


from django.db.models import signals
signals.post_save.connect(change_watcher, sender=Event, dispatch_uid='partytime.publicsite')


class StateMailingList(models.Model):
    email = models.EmailField()
    confirmation = models.IntegerField(max_length=36)
    confirmed = models.BooleanField(default=False)
    state = models.CharField(max_length=2)

    def __unicode__(self):
        return self.state + ": " + self.email



class MailingList(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()

    def __unicode__(self):
        return self.name


class Email(models.Model):
    email = models.EmailField()
    mailing_lists = models.ManyToManyField(MailingList, through='MailingListMembership')

    def __unicode__(self):
        return self.email


class MailingListMembership(models.Model):
    mailing_list = models.ForeignKey(MailingList)
    email = models.ForeignKey(Email)
    confirmation = models.BigIntegerField()
    confirmed = models.BooleanField()

    class Meta:
        unique_together = (('mailing_list', 'email', ))

    def __unicode__(self):
        return '%s: %s' % (self.mailing_list, self.email)

    def confirmation_url(self):
        return 'http://politicalpartytime.org/emailalerts/?email=%s&confirmation=%s&list=%s' % (
                    self.email.email,
                    self.confirmation,
                    self.mailing_list.id)

    def cancellation_url(self):
        return '%s&remove=true' % self.confirmation_url()

    def send_confirmation(self):
        template = get_template('emails/confirmation.html')
        body = template.render(Context({'membership': self, 'email': self.mailing_list, }))
        email = EmailMultiAlternatives('Confirm your PoliticalPartyTime.org e-mail subscription',
                                       body,
                                       'Party Time <bounce@politicalpartytime.org>',
                                       [self.email.email, ])
        email.attach_alternative(body, 'text/html')
        email.send()


class CookRating(models.Model):
    BODY_CHOICES = (
        ('H', 'House'),
        ('S', 'Senate'),
    )

    body = models.CharField(max_length=1, choices=BODY_CHOICES, blank=True, default='')
    state = models.CharField(max_length=2)
    district = models.CharField(max_length=3)
    rating = models.CharField(max_length=100)
    as_of = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = (('body', 'state', 'district', 'as_of'), )

    def __unicode__(self):
        return self.rating
