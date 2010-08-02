"""
Generate an e-mail when a new post is published.
"""
import datetime
import re

from django.core.mail import send_mail, EmailMultiAlternatives
from django.core.management.base import BaseCommand, CommandError
from django.template import Context
from django.template.loader import get_template

from publicsite.models import Post, MailingListMembership

class Command(BaseCommand):

    args = '<minutes>'
    help = """Generate an e-mail linking to each post published in the past <minutes> minutes. 
Meant to be run as a cronjob every <minutes> minutes."""
    requires_model_validation = False

    def handle(self, *args, **options):
        if not args:
            raise CommandError('<minutes> value is required.')

        minutes = args[0]

        try:
            minutes = float(minutes)
        except ValueError:
            raise CommandError('<minutes> must be a number.')

        if minutes <= 0:
            raise CommandError('<minutes> must be a positive number.')

        cutoff = datetime.datetime.now() - datetime.timedelta(minutes=minutes)
        posts = Post.objects.filter(post_date__gte=cutoff, post_status='publish') \
                            .order_by('post_date')
        for post in posts:
            send_email(post)


def send_email(post):
    memberships = MailingListMembership.objects.filter(mailing_list__name='New Post E-mails')
    template = get_template('emails/new_post_email.html')
    subject = 'New post: %s' % post.title
    firstgraf = remove_images(post.content.split('\n')[0].strip())

    for membership in memberships:

        email = membership.email.email
        confirmation = membership.confirmation
        context = {'post': post,
                   'firstgraf': firstgraf,
                   'email': email,
                   'confirmation': confirmation, }
        body = template.render(Context(context))
        email = EmailMultiAlternatives(subject,
                                       body,
                                       'Party Time <bounce@politicalpartytime.org>',
                                       [email, ])
        email.attach_alternative(body, 'text/html')
        email.send()


def remove_images(content):
    return re.sub(r'<img.*?/>', '', content)
