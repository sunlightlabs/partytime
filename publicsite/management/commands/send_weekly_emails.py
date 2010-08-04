import datetime

from django.core.mail import send_mail, EmailMultiAlternatives
from django.core.management.base import NoArgsCommand
from django.db.models import Q
from django.template import Context
from django.template.loader import get_template

from publicsite.models import LeadershipPosition, MailingList, Email, CommitteeMembership, Event, send_email


def send_leadership_email(category):
    """Category should be either 'committee' or 'congressional'
    """
    if category == 'committee':
        leadership_ids = CommitteeMembership.objects.values_list('member', flat=True).exclude(position='Member')
        mailing_list = 'All committee leadership'
        subject = 'Committee leadership fundraisers'
    else:
        leadership_ids = LeadershipPosition.objects.values_list('lawmaker', flat=True)
        mailing_list = 'Congressional leadership'
        subject = 'Congressional leadership fundraisers'

    mailing_list = MailingList.objects.get(name=mailing_list)

    events = Event.objects.filter(
                    (Q(beneficiaries__in=leadership_ids) | Q(other_members__in=leadership_ids)) &
                    Q(added__gte=datetime.date.today() - datetime.timedelta(7))
                ).distinct().order_by('-start_date', 'start_time')

    if not events:
        return

    template = 'emails/all_leadership_email.html'

    for subscriber in mailing_list.email_set.filter(mailinglistmembership__confirmed=True):
        membership = subscriber.mailinglistmembership_set.get(mailing_list=mailing_list)
        context = {'events': events,
                   'email': subscriber.email,
                   'confirmation': membership.confirmation,
                   'subject': subject, 
                   'list_id': mailing_list.pk, 
                   'cancellation_url': membership.cancellation_url(),
                   }
        send_email(template, context)


def send_committee_leadership_emails():
    """To be sent weekly. Users will subscribe to receive
    information on the leadership of one or more committees.
    We will aggregate those subscriptions by user so that
    each user receives only a single e-mail for specific
    committee leadership.
    """
    template = 'emails/leadership_email.html'
    mailing_lists = MailingList.objects.filter(name__startswith=('Committee leadership'))
    subscribers = Email.objects.filter(mailing_lists__in=mailing_lists).distinct()

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

        if not events_for_subscriber:
            continue

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
                   'subject': 'PoliticalPartyTime: Committee leadership fundraisers',
                   'list_id': mailing_list.pk,
                   'cancellation_url': membership.cancellation_url(),
                   }
        send_email(template, context)


class Command(NoArgsCommand):

    help = 'Send e-mails listing leadership events'
    requires_model_validation = False

    def handle_noargs(self, **options):
        send_committee_leadership_emails()
        send_leadership_email('committee')
        send_leadership_email('congressional')
