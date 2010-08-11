from django.core.management.base import NoArgsCommand
from django.db.utils import IntegrityError

from publicsite.models import StateMailingList, MailingListMembership, MailingList, Email


class Command(NoArgsCommand):

    help = """Convert state e-mail subscribers from the old model (StateMailingList) 
to the new (MialingList, Email and MailingListMembership)"""
    requires_model_validation = False

    def handle_noargs(self, **options):
        state_subscriptions = StateMailingList.objects.filter(confirmed=True).exclude(email__icontains='rosiak')
        for subscription in state_subscriptions:
            mailing_list = MailingList.objects.get(name=subscription.state)
            email, created = Email.objects.get_or_create(email=subscription.email)

            try:
                MailingListMembership.objects.create(mailing_list=mailing_list,
                                                     email=email,
                                                     confirmation=subscription.confirmation,
                                                     confirmed=subscription.confirmed)
            except IntegrityError:
                continue
