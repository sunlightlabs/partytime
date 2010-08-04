from django.template.loader import render_to_string
from publicsite.models import Event, MailingList, LeadershipPosition
from django.conf import settings
from django import template
import random

register = template.Library()

@register.simple_tag
def upcoming_events():
    docset = Event.objects.upcoming(5)
    return render_to_string("publicsite/upcoming_side.html", {"docset":docset})
    
@register.simple_tag
def recent_events():
    docset = Event.objects.recent(5)
    return render_to_string("publicsite/recent_side.html", {"docset":docset})


@register.filter(name='committee_position')
def committee_position(lawmaker, committee):
    """If the lawmaker has a leadership position on the
    given committee, return the position in parentheses.
    """
    position = lawmaker.committee_position(committee)
    if not position or position == 'Member':
        return ''

    return ' (%s)' % position


class LeadershipMailingListNode(template.Node):
    def render(self, context):
        lists = [{'committee': x.name.replace('Committee leadership - ', ''), 'id': x.id} 
                 for x in 
                 MailingList.objects.filter(name__startswith=('Committee leadership')).order_by('-name')]
        all_leadership = MailingList.objects.get(name='All committee leadership')
        lists.append({'committee': 'All committees', 'id': all_leadership.id})
        lists.reverse()
        context['committee_leader_mailing_lists'] = lists

        context['congressional_leader_positions'] = LeadershipPosition.objects.values_list('position', flat=True).order_by('position')
        context['congressional_leader_email_id'] = MailingList.objects.get(name='Congressional leadership').id
        context['new_post_email_id'] = MailingList.objects.get(name='New Post E-mails').id
        return ''

@register.tag
def get_leadership_mailing_lists(parser, token):
    return LeadershipMailingListNode()

