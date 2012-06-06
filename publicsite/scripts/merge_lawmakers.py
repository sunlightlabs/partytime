""" Hack to count appearance of lawmaker ids so we can kill unused dupes. """

import sys

from django.core.management import setup_environ
sys.path.append('/Users/jfenton/partytime/partytime')

import settings
setup_environ(settings)

from publicsite.models import *

from dateutil.parser import parse as dateparse

#test with some known dupes.
crp_ids = ['N00031127', 'N00031124', 'N00029131','N00031244']

for crp_id in crp_ids:
    print "\n\n!!! Looking for crp id: %s" % (crp_id)
    lawmakers = Lawmaker.objects.filter(crp_id=crp_id)

    for lawmaker in lawmakers:
    
        id_appearances = 0
    
        print "Processing id %s name: '%s' affiliate: '%s'" % (lawmaker.id, lawmaker.name, lawmaker.affiliate)
        ehs = Event.objects.filter(hosts=lawmaker)
        print "Found %s events hosted by this lawmaker" % (len(ehs))
        id_appearances += len(ehs)
    
        tags = Event.objects.filter(tags=lawmaker)
        print "Found %s events tagged with this lawmaker" % (len(tags))
        id_appearances += len(ehs)
    
        beneficiaries = Event.objects.filter(beneficiaries=lawmaker)
        print "Found %s events benefitting this lawmaker" % (len(beneficiaries))
        id_appearances += len(beneficiaries)
    
        oms= Event.objects.filter(other_members=lawmaker)
        print "Found %s events with this lawmaker as an other members" % (len(oms))
        id_appearances += len(oms)
    
        scs = SuperCommitteeMember.objects.filter(lawmaker=lawmaker)
        print "Found %s supercommittee members with this lawmaker" % (len(scs))
        id_appearances += len(scs)
    
        lps  = LeadershipPosition.objects.filter(lawmaker=lawmaker)
        print "Found %s leadership positions with this lawmaker" % (len(lps))
        id_appearances += len(lps)
    
        cs = Committee.objects.filter(members=lawmaker)
        print "Found %s committees for this lawmaker" % (len(cs))    
        id_appearances += len(cs)
    
        cms = CommitteeMembership.objects.filter(member=lawmaker)
        print "Found %s committee memberships for this lawmaker" % (len(cms))    
        id_appearances += len(cms)
    
        os = OtherInfo.objects.filter(lawmaker_id = lawmaker.id)
        print "Found %s committee memberships for this lawmaker" % (len(os))      
        id_appearances += len(os)
    
        print "Total is %s\ns" % (id_appearances)