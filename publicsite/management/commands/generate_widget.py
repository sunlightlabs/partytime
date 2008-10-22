from django.conf import settings
from django.core.management.base import NoArgsCommand
from django.template.loader import render_to_string
from publicsite.models import Event
from boto.s3 import connection, key
import boto
import random

class Command(NoArgsCommand):
    
    help = "Generates and uploads ABC News widget"
    
    requires_model_validation = False
    
    def handle_noargs(self, **options):
        
        conn = connection.S3Connection(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
        bucket = conn.create_bucket(settings.AWS_BUCKET)
        
        conventions = (
            ('republican','gop convention'),
            ('democratic','democratic convention'),
        )
        
        for convention, args in conventions:
        
            events = Event.objects.filter(status='', tags=args)
            event_count = events.count()
        
            if event_count > 0:
            
                randdocnum = random.randint(0, event_count - 1)
                event = events[randdocnum]
                content = render_to_string("publicsite/widgets/abc_convention.html",
                    {"field":"Tags", "args": args, "doc":event, "convention": convention})
    
                k = key.Key(bucket)
                k.key = 'abc/%s.html' % convention
                k.set_contents_from_string(content, headers={"Content-Type": "text/html"}, replace=True)
                k.set_acl('public-read')