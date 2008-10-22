from django.template.loader import render_to_string
from publicsite.models import Event
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
