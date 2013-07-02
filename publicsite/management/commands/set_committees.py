import json, os

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from publicsite.models import Lawmaker, Committee, CommitteeMembership

PROJECT_ROOT = getattr(settings, 'PROJECT_ROOT')
json_file = os.path.join(PROJECT_ROOT, 'import_data', 'current_committee_members.json')

class Command(BaseCommand):
    help = "Create committees, committee membership. July 2, 2013"
    
    requires_model_validation = False

    def handle(self, *args, **options):
        infile = open(json_file, 'r')
        committees = json.loads(infile.read())
        
        for committee in committees:
            
            
            # add the committee
            committeemodel = None
            try: 
                committeemodel= Committee.objects.get(short=committee['thomas_id'])
            except Committee.DoesNotExist:
                
                ctype = "House"
                if committee['committee_type'] == 'senate':
                    ctype = "Senate"
                elif committee['committee_type'] == 'join':
                    ctype = "Joint"
                committeemodel = Committee.objects.create(
                    short=committee['thomas_id'],
                    title=committee['name'],
                    chamber=ctype
                    )
                    
            # Now add the members
            
            for member in committee['members']:
                membermodels = None
                membermodels = Lawmaker.objects.filter(bioguide=member['bioguide'])
                if len(membermodels)==0:
                    print "Couldn't find %s %s -- maybe bioguide %s isn't assigned?" % (member['first_name'], member['last_name'], member['bioguide'])
                    continue
                
                for membermodel in membermodels:
                    # Create a new committee membership
                    try:
                        CommitteeMembership.objects.get(committee=committeemodel, member=membermodel)
                    except CommitteeMembership.DoesNotExist:
                        CommitteeMembership.objects.create(
                            committee=committeemodel,
                            member=membermodel,
                            position=member.get('title'),
                            )