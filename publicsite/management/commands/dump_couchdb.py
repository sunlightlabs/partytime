from django.conf import settings
from django.core.management.base import NoArgsCommand
from publicsite.couchdb import Couch
import simplejson
    
class Command(NoArgsCommand):
    
    help = "Dump couchdb database to stdout"
    
    requires_model_validation = False
    
    def handle_noargs(self, **options):
        
        query = """function(doc) { map(null, doc); }"""
        
        c = Couch(settings.COUCHDB_HOST, settings.COUCHDB_PORT)
        print c.adHoc(settings.PARTYTIME_DB, query, 10000, '', raw=True)