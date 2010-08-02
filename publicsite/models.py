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

import scribd

from settings import SCRIBD_KEY, SCRIBD_SECRET

from sunlightapi import sunlight, SunlightApiError
sunlight.apikey = '***REMOVED***'


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
        sql = """SELECT t.name,
                        t.slug
                    FROM wp_terms t
                    INNER JOIN wp_term_taxonomy tt
                        ON t.term_id = tt.term_id
                    INNER JOIN wp_term_relationships tr
                        ON tt.term_taxonomy_id = tr.term_taxonomy_id
                    WHERE tt.taxonomy = %s
                        AND
                          tr.object_id = %s
                  ORDER BY tr.term_order"""
        cursor = connection.cursor()
        cursor.execute(sql, [taxonomy, self.id])
        return [{'name': row[0], 'slug': row[1]} for row in cursor.fetchall()]

    def save(self):
        pass

    def delete(self):
        pass


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
                    start_date__gte=datetime.datetime.now(),
                    status='').order_by('start_date', 'start_time')[:limit]
        return events

    def daterange(self, start, end):
        startdate = datetime.datetime(int(start[0:4]), int(start[4:6]), int(start[6:8]))
        enddate = datetime.datetime(int(end[0:4]), int(end[4:6]), int(end[6:8]))
        events = Event.objects.filter(
                    start_date__gte=startdate, start_date__lte=enddate,
                    status='').order_by('start_date', 'start_time')
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

    def leadership_positions(self):
        return self.committeemembership_set.filter(Q(position='Chair') |
                                                   Q(position='Vice Chair') |
                                                   Q(position='Ranking Member'))



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
        if self.entertainment:
            title += self.entertainment
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

        description = ("This is an invitation for a political fundraiser on %s. "
                       "Get details at Sunlight Foundation's "
                       "<a href=\"%s\">Party Time</a>"
                       ) % (self.start_date.strftime('%B %d, %Y'), event_url)

        params = {'title': self.event_title(),
                  'publisher': "Sunlight Foundation's Party Time",
                  'description': description,
                  # The link_back_url will work only for Scribd Qualified Publishers.
                  'link_back_url': event_url,
                  'tags': self.make_scribd_tags(),
                  'category': 'Government Docs',
                  'access': 'public',
                  }

        scribd.update([doc,], **params)

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

        for beneficiary in self.beneficiaries.exclude(Q(state__isnull=True) | Q(state='')):
            subject = 'PoliticalPartyTime: Fundraiser for %s on %s' % (unicode(beneficiary),
                                                                       self.start_date.strftime('%B %d, %Y'))
            template = 'emails/party_description.html'
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
                           'subject': subject, }
                self._send_email(template, context)


    def send_all_committee_leadership_email(self):
        """To be sent weekly.
        """
        events = Event.objects.filter(
                (Q(beneficiaries__committeemembership__position__icontains='chair') |
                 Q(beneficiaries__committeemembership__position='Ranking Member')) &
                Q(added__gte=datetime.date.today() - datetime.timedelta(7))
            ).order_by('start_date').distinct()

        mailing_list = MailingList.objects.get(name='All committee leadership')
        template = 'emails/all_leadership_email.html'

        for subscriber in mailing_list.email_set.filter(mailinglistmembership__confirmed=True):
            membership = subscriber.mailinglistmembership_set.get(mailing_list=mailing_list)
            context = {'events': events,
                       'email': subscriber.email,
                       'confirmation': membership.confirmation,
                       'subject': 'PoliticalPartyTime: Committee leadership fundraisers', }
            self._send_email(template, context)


    def send_committee_leadership_emails(self):
        """To be sent weekly. Users will subscribe to receive
        information on the leadership of one or more committees.
        We will aggregate those subscriptions by user so that
        each user receives only a single e-mail for specific
        committee leadership.
        """
        template = 'emails/leadership_email.html'
        mailing_lists = MailingList.objects.filter(name__startswith=('Committee leadership'))
        subscribers = Email.objects.filter(mailing_lists=mailing_lists).distinct()

        for subscriber in subscribers:
            memberships = subscriber.mailinglistmembership_set.filter(confirmed=True,
                                                                      mailing_list__in=mailing_lists)
            events_for_subscriber = []

            for membership in memberships:
                mailing_list = membership.mailing_list
                committee = Committee.objects.get(title=mailing_list.name.replace('Committee leadership - ', ''))
                leadership_ids = committee.leadership_members().values_list('member', flat=True)
                events = Event.objects.filter(beneficiaries__in=leadership_ids,
                                              added__gte=datetime.date.today() - datetime.timedelta(7)
                                          ).order_by('start_date')
                events_for_subscriber += events

            events = sorted(set(events), cmp=lambda x, y: cmp(x.start_date, y.start_date))

            # Because there are multiple memberships being included
            # in a single e-mail, and each membership has its own
            # confirmation code, we send the first membership's
            # confirmation code as the one with which the recipient
            # can cancel the e-mail. We warn users in the template
            # that clicking the unsubscribe link will unsubscribe them from
            # all the specific committee leadership e-mails.
            context = {'events': events,
                       'email': recipient.email,
                       'confirmation': memberships[0].confirmation,
                       'subject': 'PoliticalPartyTime: Committee leadership fundraisers', }
            self._send_email(template, context)


    def _send_email(self, template, context):
        template = get_template(template)
        body = template.render(Context(context))
        email = EmailMultiAlternatives(context['subject'],
                                       body,
                                       'Party Time <bounce@politicalpartytime.org>',
                                       [context['email'], ])
        email.attach_alternative(body, 'text/html')
        email.send()


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
    confirmation = models.IntegerField(max_length=36)
    confirmed = models.BooleanField()

    class Meta:
        unique_together = (('mailing_list', 'email', ))

    def __unicode__(self):
        return '%s: %s' % (self.mailing_list, self.email)



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
