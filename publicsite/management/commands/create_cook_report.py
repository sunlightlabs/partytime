import csv
import datetime
import re
import sys

from django.core.management.base import NoArgsCommand

from publicsite.models import *

from sunlightapi import sunlight
sunlight.apikey = '***REMOVED***'


class Command(NoArgsCommand):

    help = "Create a CSV of party data with Cook Report ratings"

    requires_model_validation = False

    def handle_noargs(self, **options):

        fields = ['Cook Report Rating',
                  'Invitation_URL',
                  'Beneficiary',
                  'Host',
                  'Other Members',
                  'Start_Date',
                  'Start_Time',
                  'End_Date',
                  'End_Time',
                  'Entertainment',
                  'Venue_Name',
                  'Venue_Address1',
                  'Venue_Address2',
                  'Venue_City',
                  'Venue_State',
                  'Venue_Zipcode',
                  'Venue_Website',
                  'LatLong',
                  'Contributions_Info',
                  'Make_Checks_Payable_To',
                  'Checks_Payable_To_Address',
                  'Committee_Id',
                  'RSVP_Info',
                  'Distribution_Paid_for_By',
                  'Canceled',
                  'Postponed', ]
        csv.writer(sys.stdout).writerow(fields)

        events = Event.objects.filter(start_date__gte=datetime.date(2010, 07, 01)).order_by('start_date')

        for event in events:

            cook_rating = None

            beneficiaries = event.beneficiaries.all()
            if not beneficiaries:
                continue

            beneficiary = beneficiaries[0]
            if not beneficiary.district:

                if beneficiary.state: # Senate
                    body = 'S'
                    district = ''

                elif beneficiary.affiliate: # PAC w/ affiliate
                    # Search for legislator w/ Sunlight Congress API
                    affiliate = re.sub(r'\(.*$', '', beneficiary.affiliate) # Remove affiliation & district
                    matches = sunlight.legislators.search(affiliate, threshold=.99)
                    if matches:
                        legislator = matches[0].legislator
                        state = legislator.state
                        district = legislator.district

                        if district == 'Senior Seat' or district == 'Junior Seat': # Senate
                            body = 'S'
                            district = ''

                        else:
                            body = 'H'

                    else:
                        cook_rating = 'unable to find race'

                else: # PAC w/o affiliate
                    cook_rating = 'PAC listed with no affiliate'

            else:
                state = beneficiary.state
                district = beneficiary.district
                body = 'H'


            if not cook_rating and body is not 'S':
                rating = CookRating.objects.filter(body=body,
                                                   state=state,
                                                   district=district) \
                                           .order_by('-as_of')

                if rating:
                    cook_rating = rating[0]
                else:
                    cook_rating = ''

            row = [cook_rating,
                    'http://politicalpartytime.org%s' % event.get_absolute_url(),
                    beneficiary.__unicode__(),
                    ' || '.join([x.__unicode__() for x in event.hosts.all()]),
                    ' || '.join([x.__unicode__() for x in event.other_members.all()]),
                    event.start_date or '',
                    event.start_time or '',
                    event.end_date or '',
                    event.end_time or '',
                    event.entertainment or '',
                    event.venue.venue_name if event.venue else '',
                    event.venue.address1 if event.venue else '',
                    event.venue.address2 if event.venue else '',
                    event.venue.city if event.venue else '',
                    event.venue.state if event.venue else '',
                    event.venue.zipcode if event.venue else '',
                    event.venue.website if event.venue else '',
                    '%s;%s' % (event.venue.latitude,
                               event.venue.longitude) if event.venue else '',
                    event.contributions_info,
                    event.make_checks_payable_to,
                    event.checks_payable_to_address,
                    event.committee_id,
                    event.rsvp_info,
                    event.distribution_paid_for_by,
                    event.canceled or '',
                    event.postponed or '',
                    ]

            try:
                csv.writer(sys.stdout).writerow(row) 
            except UnicodeEncodeError:
                continue
