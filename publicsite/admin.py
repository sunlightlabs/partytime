from django.contrib import admin
from publicsite.models import *

from publicsite.widgets import ManyToManyAdmin    

class EventAdmin(ManyToManyAdmin):

  
    list_display = ('id', 'start_date', 'entertainment', 'venue', 'status')


    ajax_manytomany_fields={'hosts':('name'), 'beneficiaries':('name'), 'other_members':('name')}


    fieldsets = (
        (None, {
            'fields': (('start_date', 'start_time', 'end_date', 'end_time'), 'entertainment', 'venue')
        }),
        (None, {
            'fields': ('hosts', 'beneficiaries', 'other_members')
        }),
        (None, {
            'fields': (            
                'rsvp_info',
                ('event_paid_for_by', 'distribution_paid_for_by'),
                ('make_checks_payable_to', 'checks_payable_to_address'),
                'contributions_info',
                ('data_entry_problems', 'status', 'user_initials')
            )}
            )
    )

admin.site.register(Event, EventAdmin)


admin.site.register(Lawmaker)
admin.site.register(Venue)
admin.site.register(Entertainment)
admin.site.register(Host)

"""
class Event(models.Model):
    def __unicode__(self):
        return self.other_info
    objects = EventManager()

    entertainment = models.ForeignKey(Entertainment,null=True)
    venue = models.ForeignKey(Venue,null=True)

    hosts = models.ManyToManyField(Host,db_table=u'publicsite_event_hosts')
    tags = models.ManyToManyField(Tag,db_table=u'publicsite_event_tags')
    beneficiaries = models.ManyToManyField(Lawmaker,db_table=u'publicsite_event_beneficiary', related_name='publicsite_event_beneficiary')
    other_members = models.ManyToManyField(Lawmaker,db_table=u'publicsite_event_omc', related_name='publicsite_event_omc')
     
    start_date = models.DateField(blank=True, null=True)
    start_time = models.TimeField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)

    status = models.CharField(blank=True, max_length=255, db_index=True)    
    pdf_document_link = models.CharField(blank=True, max_length=255)
    committee_id = models.CharField(blank=True, max_length=255)    
    rsvp_info = models.CharField(blank=True, max_length=255)
    event_paid_for_by = models.CharField(blank=True, max_length=255)
    distribution_paid_for_by = models.CharField(blank=True, max_length=255)
    make_checks_payable_to = models.CharField(blank=True, max_length=255)
    checks_payable_to_address = models.CharField(blank=True, max_length=255)
    contributions_info = models.CharField(blank=True, max_length=255)
    user_initials = models.CharField(blank=True, max_length=32)
    data_entry_problems = models.TextField(blank=True)
"""






















