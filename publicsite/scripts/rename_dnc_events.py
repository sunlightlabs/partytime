""" Hack to count appearance of lawmaker ids so we can kill unused dupes. """

import sys, re

from django.core.management import setup_environ
sys.path.append('/projects/partytime/src/partytime/')
#sys.path.append('/Users/jfenton/partytime/partytime')

import settings
setup_environ(settings)

from publicsite.models import *

from dateutil.parser import parse as dateparse


#events = Event.objects.daterange('20120825', '20120902')

events = Event.objects.daterange('20120628', '20120909')

convention_event = re.compile("\s*Democratic Convention --\s*", re.I)

for event in events:
    match = re.match(convention_event, event.entertainment)
    if match:
        
        print '%s|%s|%s|%s' % (event.pk, event.entertainment, event.start_date, event.venue.venue_name)
        
        fixed_name = re.sub(convention_event, "", event.entertainment)
        fixed_name = fixed_name + " -- Democratic Convention"
        
        print "Proposed replacement name: %s" % (fixed_name)
        
        event.entertainment = fixed_name
        #event.save()