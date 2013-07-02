import json, os

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from publicsite.models import Lawmaker

PROJECT_ROOT = getattr(settings, 'PROJECT_ROOT')
json_file = os.path.join(PROJECT_ROOT, 'import_data', 'leg_crosswalk.json')

class Command(BaseCommand):
    help = "Add bioguide ids, based on a crosswalk file, when available"
    
    requires_model_validation = False

    def handle(self, *args, **options):
        infile = open(json_file, 'r')
        crosswalk = json.loads(infile.read())
        
        # hash the legislators on the basis of their CRP ids so we can look them up
        leg_dict = {}
        for leg in crosswalk:
            if leg['opensecrets']:
                leg_dict[leg['opensecrets']]=leg['bioguide']
        
        # Now look up the lawmakers who don't have a CRP id and add it.
        lawmakers = Lawmaker.objects.filter(bioguide__isnull=True)
        found=0
        notfound=0
        crp_id_missing = 0
        for lawmaker in lawmakers:
            bioguide_id = None
            try:
                bioguide_id = leg_dict[lawmaker.crp_id]
                #print "Found bioguide %s for %s" % (bioguide_id, lawmaker)
                found += 1
                lawmaker.bioguide = bioguide_id
                lawmaker.save()
                
            except KeyError:
                if lawmaker.crp_id and lawmaker.crp_id.startswith('N'):
                    notfound += 1
                    print "Missing for %s, crp_id = %s" % (lawmaker, lawmaker.crp_id)
                else:
                    crp_id_missing += 1
        print "Result: found=%s, notfound=%s, no crp id: %s" % (found, notfound, crp_id_missing)