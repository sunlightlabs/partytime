from tastypie.resources import ModelResource, ALL, ALL_WITH_RELATIONS
from tastypie import fields

from django.conf import settings
from django.http import HttpResponse
from tastypie.utils.mime import determine_format, build_content_type

from publicsite.models import Lawmaker, Venue, Event, Host

from api_authentication import LocksmithKeyAuthentication
from models import LogEntry

API_LIMIT_PER_PAGE = getattr(settings, 'API_LIMIT_PER_PAGE', 50)


class LawmakerResource(ModelResource):
    class Meta:
        filtering = {'crp_id':ALL, 'state':ALL,}
        max_limit = API_LIMIT_PER_PAGE
        queryset = Lawmaker.objects.all()
        resource_name = 'lawmaker'
        authentication = LocksmithKeyAuthentication()
        
class VenueResource(ModelResource):
    class Meta:
        API_LIMIT_PER_PAGE = API_LIMIT_PER_PAGE
        queryset = Venue.objects.all()
        resource_name = 'venue'
        excludes = ['latitude', 'longitude', 'website', 'townhouse']
        authentication = LocksmithKeyAuthentication()        
        
class HostResource(ModelResource):
    class Meta:
        max_limit = API_LIMIT_PER_PAGE
        queryset = Host.objects.all()
        resource_name = 'host'
        filtering = {'crp_id':ALL,'id':ALL,}
        authentication = LocksmithKeyAuthentication()        

        
class EventResource(ModelResource):
    venue = fields.ForeignKey(VenueResource, 'venue', full=True, null=True)
    beneficiaries = fields.ManyToManyField(LawmakerResource, 'beneficiaries', full=True, null=True)
    hosts = fields.ManyToManyField(HostResource, 'hosts', full=True, null=True)
        
    class Meta:
        filtering = {'beneficiaries':ALL_WITH_RELATIONS, 'hosts':ALL_WITH_RELATIONS,}
        max_limit = API_LIMIT_PER_PAGE
        queryset = Event.objects.all()
        resource_name = 'event'
        excludes = ['data_entry_problems', 'user_initials', 'status', 'tags', 'pdf_document_link', 'committee_id', 'scribd_upload', 'scribd_id', 'scribd_url', 'added']
        authentication = LocksmithKeyAuthentication()
        
