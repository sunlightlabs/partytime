from django.contrib import admin
from publicsite.models import *

import widgets

class EventAdmin(widgets.AutocompleteModelAdmin):
    fieldsets = (
        (None, {
            'fields': (('start_date', 'start_time'), ('end_date', 'end_time'), 'entertainment', 'venue',  'pdf_document_link')
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
    related_search_fields = { 
		'hosts': ('name',),
		#'venue': ('listname',),
        'venue': ('venue_name', 'venue_address'),
        'entertainment': ('entertainment_type',),   
        'beneficiaries': ('name',),
        'other_members': ('name',),
    }

    list_display = ('id', 'start_date', 'entertainment', 'venue', 'status',)
    list_filter = ('status',)





admin.site.register(Event, EventAdmin)
admin.site.register(Venue)
admin.site.register(Host)
admin.site.register(Lawmaker)
admin.site.register(Entertainment)

