from django.contrib import admin
from publicsite.models import *


from publicsite.widgets import ManyToManyAdmin    

class EventAdminWid(ManyToManyAdmin):

  
    list_display = ('id', 'start_date', 'entertainment', 'venue', 'status')
    list_filter = ('status',)


    ajax_manytomany_fields={'hosts':('name'), 'beneficiaries':('name'), 'other_members':('name')}


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







from publicsite.widgets import ForeignKeySearchInput



class EventAdmin(EventAdminWid):
    related_search_fields = {
        'venue': ('name', ),
        'entertainment': ('entertainment_type', ),
    }

    def get_urls(self):
        urls = super(EventAdmin,self).get_urls()
        search_url = patterns('', (r'^search/$', self.search))
        return search_url + urls

    def search(self, request):
        """
        Searches in the fields of the given related model and returns the 
        result as a simple string to be used by the jQuery Autocomplete plugin
        """
        query = request.GET.get('q', None)
        app_label = request.GET.get('app_label', None)
        model_name = request.GET.get('model_name', None)
        search_fields = request.GET.get('search_fields', None)

        if search_fields and app_label and model_name and query:
            def construct_search(field_name):
                # use different lookup methods depending on the notation
                if field_name.startswith('^'):
                    return "%s__istartswith" % field_name[1:]
                elif field_name.startswith('='):
                    return "%s__iexact" % field_name[1:]
                elif field_name.startswith('@'):
                    return "%s__search" % field_name[1:]
                else:
                    return "%s__icontains" % field_name

            model = models.get_model(app_label, model_name)
            qs = model._default_manager.all()
            for bit in query.split():
                or_queries = [models.Q(**{construct_search(
                    smart_str(field_name)): smart_str(bit)})
                        for field_name in search_fields.split(',')]
                other_qs = QuerySet(model)
                other_qs.dup_select_related(qs)
                other_qs = other_qs.filter(reduce(operator.or_, or_queries))
                qs = qs & other_qs
            data = ''.join([u'%s|%s\n' % (f.__unicode__(), f.pk) for f in qs])
            return HttpResponse(data)
        return HttpResponseNotFound()

    def formfield_for_dbfield(self, db_field, **kwargs):
        """
        Overrides the default widget for Foreignkey fields if they are
        specified in the related_search_fields class attribute.
        """
        if isinstance(db_field, models.ForeignKey) and \
                db_field.name in self.related_search_fields:
            kwargs['widget'] = ForeignKeySearchInput(db_field.rel,
                                    self.related_search_fields[db_field.name])
        return super(EventAdmin, self).formfield_for_dbfield(db_field, **kwargs)



admin.site.register(Event, EventAdmin)


admin.site.register(Lawmaker)
admin.site.register(Venue)
admin.site.register(Entertainment)
admin.site.register(Host)












