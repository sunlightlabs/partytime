from cStringIO import StringIO
import csv
import zipfile

from django.core.management.base import NoArgsCommand
from django.db.models import Q
from django.utils.encoding import smart_str

from publicsite.models import *


def clean_row(row):
    return [smart_str(x) if x else '' for x in row]


def get_events():
    fields = ['id',
              'canceled',
              'postponed',
              'start_date',
              'end_date',
              'start_date',
              'end_time',
              'entertainment',
              'venue_id',
              'contributions_info',
              'make_checks_payable_to',
              'checks_payable_to_address',
              'committee_id',
              'rsvp_info',
              'distribution_paid_for_by', ]
    events = Event.objects.values_list(*fields).filter(Q(status='') | Q(status=None))
    fields[0] = 'url'
    data = [fields, ]

    # Need to loop through events to encode them correctly for CSV output.
    for event in events:
        event = ['http://politicalpartytime.org/party/%s' % event[0], ] + list(event)
        data.append(clean_row(event))

    return data


def get_venues():
    fields = ['id',
              'venue_name',
              'address1',
              'address2',
              'city',
              'state',
              'zipcode',
              'latitude',
              'longitude', ]
    venues = Venue.objects.values_list(*fields)
    data = [fields, ]

    # Need to loop through venues to encode them correctly for CSV output.
    for venue in venues:
        data.append(clean_row(venue))

    return data


def m2m_tables(**kwargs):
    data = []

    events = Event.objects.values_list('id', 'canceled', 'postponed').filter(Q(status='') | Q(status=None))
    for event in events:
        values = kwargs['model'].objects.values_list(*kwargs['model_fields']).filter(**{kwargs['filter_field']: event[0]})
        for result in values:
            data.append(clean_row(event) + clean_row(result))

    return [kwargs['fields'], ] + data


def get_m2m_data():
    objs = [{'fields': ['event_id',
                        'canceled',
                        'postponed',
                        'beneficiary_id',
                        'beneficiary_name',
                        'party',
                        'state',
                        'district',
                        'crp_id', ],
             'model_fields': ['id', 'name', 'party', 'state', 'district', 'crp_id', ],
             'filter_field': 'pol_events',
             'model': Lawmaker,
             'filename': 'beneficiaries.csv', },

             {'fields': ['event_id', 'canceled', 'postponed', 'host_id', 'host_name', ],
              'model_fields': ['id', 'name', ],
              'filter_field': 'event',
              'model': Host,
              'filename': 'hosts.csv', },

             {'fields': ['event_id',
                         'canceled',
                         'postponed',
                         'omc_id',
                         'omc_name',
                         'party',
                         'state',
                         'district', ],
              'model_fields': ['id', 'name', 'party', 'state', 'district'],
              'filter_field': 'pol_appearances',
              'model': Lawmaker,
              'filename': 'omcs.csv', },
            ]

    return [(obj['filename'], m2m_tables(**obj), ) for obj in objs]


def create_zipfile():
    # Generate the CSV files to go in the ZIP file.
    zbuffer = StringIO()
    zfile = zipfile.ZipFile(zbuffer, 'w', zipfile.ZIP_DEFLATED)

    data = [('events.csv', get_events(), ),
            ('venues.csv', get_venues(), ),
            ]

    data += get_m2m_data()

    for filename, rows in data:
        print 'Generating %s' % filename
        fbuffer = StringIO()
        writer = csv.writer(fbuffer)
        writer.writerows(rows)
        zfile.writestr(filename, fbuffer.getvalue())
        fbuffer.close()

    zfile.close()
    zbuffer.flush()

    flob = open('partytime_dump.zip', 'wb')
    flob.write(zbuffer.getvalue())
    flob.close()

    zbuffer.close()


def dump_all():
    fields = ['key', 'Beneficiary', 'Host', 'Other Members', 'Start_Date', 'End_Date', 
              'Start_Time', 'End_Time',	'Entertainment', 'Venue_Name',	
              'Venue_Address1', 'Venue_Address2', 'Venue_City', 'Venue_State',
              'Venue_Zipcode', 'Venue_Website', 'LatLong', 'Contributions_Info',	
              'Make_Checks_Payable_To', 'Checks_Payable_To_Address', 'Committee_Id', 
              'RSVP_Info', 'Distribution_Paid_for_By', 'CRP_ID', 'Canceled', 'Postponed', 'CRP_ID', ]
    rows = [fields, ]

    events = Event.objects.filter(Q(status='') | Q(status=None)).select_related()
    for event in events:
        venue = event.venue
        row = [event.id,
               ' || '.join([str(x) for x in event.beneficiaries.all()]),
               ' || '.join([str(x) for x in event.hosts.all()]),
               ' || '.join([str(x) for x in event.other_members.all()]),
               event.start_date or '',
               event.start_time or '',
               event.end_date or '',
               event.end_time or '',
               event.entertainment, ]

        if venue:
            row += [venue.venue_name,
                    venue.address1,
                    venue.address2,
                    venue.city,
                    venue.state,
                    venue.zipcode,
                    venue.website,
                    ','.join([str(venue.latitude), str(venue.longitude)]) if venue.latitude else '',
                   ]
        else:
            row += ['', ] * 8

        row += [event.contributions_info,
                event.make_checks_payable_to,
                event.committee_id,
                event.rsvp_info,
                event.distribution_paid_for_by,
                event.canceled or '',
                event.postponed or '', 
                '||'.join([str(x.crp_id) for x in event.beneficiaries.all() if x.crp_id]),
                ]

        try:
            rows.append(clean_row(row))
        except UnicodeDecodeError:
            print row

    writer = csv.writer(open(r'partytime_dump_all.csv', 'w'))
    writer.writerows(rows)


class Command(NoArgsCommand):

    help = "Dump Party Time bulk data."
    requires_model_validation = False

    def handle_noargs(self, **options):
        #create_zipfile()
        dump_all()
