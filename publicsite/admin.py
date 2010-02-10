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
                ('distribution_paid_for_by'),
                ('make_checks_payable_to', 'checks_payable_to_address'),
                'contributions_info',
                ('data_entry_problems', 'status', 'user_initials')
            )}
            )
    )
    related_search_fields = { 
		'hosts': ('name',),
        'venue': ('venue_name', 'address1'),
        'beneficiaries': ('name',),
        'other_members': ('name',),
    }

    list_display = ('id', 'start_date', 'entertainment', 'venue', 'status',)
    list_filter = ('status',)




class VenueAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': (
                'venue_name',
                'address1', 'address2',
                ('city', 'state', 'zipcode'),
            )}
            ),
    )


admin.site.register(Event, EventAdmin)
admin.site.register(Venue, VenueAdmin)
admin.site.register(Host)
admin.site.register(Lawmaker)


