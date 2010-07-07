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
        ),
        (None, {
            'fields': (
                ('postponed'),
            )}
        ),
        (None, {
            'fields': (
                ('canceled'),
            )}
        ),
    )

    related_search_fields = { 
		'hosts': ('name',),
        'venue': ('venue_name', 'address1'),
        'beneficiaries': ('name',),
        'other_members': ('name',),
    }

    list_display = ('id', 'start_date', 'entertainment', 'venue', 'status',)

    list_filter = ('status',)

    search_fields = ['venue__venue_name', 'beneficiaries__name', ]

    """
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        import datetime
        if db_field.name == 'replacement_event':
            kwargs['queryset'] = Event.objects.filter(start_date__gte=datetime.date.today())
            return db_field.formfield(**kwargs)
        return super(EventAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)
    """


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

    list_display = ('venue_name', 'city', 'state', )

    search_fields = ['venue_name', ]


class HostAdmin(admin.ModelAdmin):
    search_fields = ['name', 'crp_id', ]


class LawmakerAdmin(admin.ModelAdmin):
    pass


admin.site.register(Event, EventAdmin)
admin.site.register(Venue, VenueAdmin)
admin.site.register(Host, HostAdmin)
admin.site.register(Lawmaker, LawmakerAdmin)
