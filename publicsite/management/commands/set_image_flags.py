import json, os

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from publicsite.models import Lawmaker

PROJECT_ROOT = getattr(settings, 'PROJECT_ROOT')
json_file = os.path.join(PROJECT_ROOT, 'import_data', 'images.json')

class Command(BaseCommand):
    help = "Set image available flags, when appropriate, from json file"
    
    requires_model_validation = False

    def handle(self, *args, **options):
        infile = open(json_file, 'r')
        images = json.loads(infile.read())
        num_images_found = 0
        for bioguide in images:
            #print bioguide
            lawmakers=Lawmaker.objects.filter(bioguide=bioguide)
            for thislawmaker in lawmakers:
                thislawmaker.image_available = True
                thislawmaker.save()
                num_images_found+=1
        print "Total images found: %s" % (num_images_found)