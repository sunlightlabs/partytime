from django.contrib import admin
from publicsite.models import *
import widgets


class EventAdmin(widgets.AutocompleteModelAdmin):

    fieldsets = [
        (None, {
            'fields': (('start_date', 'start_time'), ('end_date', 'end_time'), 'entertainment', 'venue',  'pdf_document_link')
        }),
        (None, {
            'fields': ('hosts', 'beneficiaries', 'is_presidential', 'other_members')
        }),
        (None, {
            'fields': (
                'rsvp_info',
                ('distribution_paid_for_by'),
                ('make_checks_payable_to', 'checks_payable_to_address'),
                'contributions_info',
                ('data_entry_problems', 'status', 'user_initials', 'notes')
            )}
        ),
        ('Cancellations/Postponements', {
            'fields': (
                ('postponed'),
                ('canceled'),
            )}
        ),
    ]

    related_search_fields = { 
		'hosts': ('name',),
        'venue': ('venue_name', 'address1'),
        'beneficiaries': ('name',),
        'other_members': ('name',),
    }

    list_display = ('id', 'start_date', 'entertainment', 'venue', 'status',)

    list_filter = ('status', 'start_date', 'canceled', 'postponed', )

    search_fields = ['venue__venue_name', 'beneficiaries__name', ]

    date_hierarchy = 'start_date'


    def add_view(self, request, form_url='', extra_context=None):
        """Remove cancellation/postponement option on add pages;
        should only show up on change pages.

        Also remove scribd_url field from add pages.
        """
        for i, fieldset in enumerate(self.fieldsets):
            if fieldset[0] == 'Cancellations/Postponements':
                del(self.fieldsets[i])
            elif fieldset[0] == 'Scribd':
                self.fieldsets[i][1]['fields'] = ((fieldset[1]['fields'][0][0],), )

        return super(EventAdmin, self).add_view(request, form_url, extra_context)


    def change_view(self, request, object_id, extra_context=None):
        """Remove the scribd_url field from change pages
        if it's blank.
        """
        event = Event.objects.get(pk=object_id)
        if not event.scribd_url:
            for i, fieldset in enumerate(self.fieldsets):
                if fieldset[0] == 'Scribd':
                    self.fieldsets[i][1]['fields'] = ((fieldset[1]['fields'][0][0], ), )
                    break

        return super(EventAdmin, self).change_view(request, object_id, extra_context)


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
    search_fields = ['name', ]


class CookRatingAdmin(admin.ModelAdmin):
    list_display = ('body', 'state', 'district', 'rating', 'as_of', )

admin.site.register(Event, EventAdmin)
admin.site.register(Venue, VenueAdmin)
admin.site.register(Host, HostAdmin)
admin.site.register(Lawmaker, LawmakerAdmin)
admin.site.register(CookRating, CookRatingAdmin)
