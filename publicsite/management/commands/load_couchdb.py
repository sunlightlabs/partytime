from django.conf import settings
from django.core.management.base import NoArgsCommand, CommandError
from publicsite.models import Event, Beneficiary, Host, OtherMember
import datetime
import decimal
import simplejson
import re
import sys

DATE_RE = re.compile(r"(?P<month>\d{1,2})/(?P<day>\d{1,2})/(?P<year>\d{4})")
TIME_RE = re.compile(r"(?P<hour>\d{1,2}):(?P<minute>\d{2})\s*(?P<meridian>AM|PM)", re.I)
MOC_RE = re.compile(r"(?P<name>[\w\s\.]+)\s+\(((?P<party>D|R|I{1})?[\s,]*)(?P<state>\w{2})(-(?P<district>\d{1,2}))?\)", re.I)

def parse_moc(moc):
    if moc:
        parts = moc.strip().split(";")
        m = MOC_RE.match(parts[0])
        if m:
            d = m.groupdict()
            if len(parts) > 1:
                d['other_info'] = ", ".join(parts[1:])            
            for key, value in m.groupdict().items():
                if value == None:
                    d[key] = ''
            return d
    
def parse_date(date):
    if date:
        m = DATE_RE.match(date.strip())
        if m:
            d = m.groupdict()
            return datetime.date(int(d['year']), int(d['month']), int(d['day']))
    
def parse_time(time):
    if time:
        m = TIME_RE.match(time.strip())
        if m:
            d = m.groupdict()
            hour = int(d['hour'])
            if d['meridian'].upper() == "PM":
                hour = (hour + 12) % 24
            return datetime.time(hour, int(d['minute']))

class Command(NoArgsCommand):
    
    help = "Dump couchdb database to stdout"
    
    requires_model_validation = False
    
    def handle_noargs(self, **options):

        docset = simplejson.loads(sys.stdin.read())
        docs = docset['rows']

        keyset = set()

        for doc in docs:
            
            if doc['id'] == 'tags':
                continue
            
            doc_val = doc['value']

            #
            # event
            #

            event = Event(id = int(doc['id'].strip()))

            event.tags = doc_val.get('Tags', '').strip()
            event.status = doc_val.get('status', '').strip()
            event.committee_id = doc_val.get('Committee_Id', '').strip()
            event.pdf_document_link = doc_val.get('PDF_Document_Link', '').strip()

            # lat long
            ll = doc_val.get('LatLong', '').split(";")
            if ll and len(ll) > 2:
                event.latitude = ll[0]
                event.longitude = ll[1]
    
            # date and time
            event.start_date = parse_date(doc_val.get('Start_Date', '')) # parse date?
            event.start_time = parse_time(doc_val.get('Start_Time', '')) # parse time?
            event.end_date = parse_date(doc_val.get('End_Date', '')) # parse date?
            event.end_time = parse_time(doc_val.get('End_Time', ''))    # parse time?

            # venue
            event.venue_name = doc_val.get('Venue_Name', '').strip()
            event.venue_address = doc_val.get('Venue_Address', '').strip()
            event.entertainment_type = doc_val.get('Entertainment_Type', '').strip()
            event.special_guest = doc_val.get('Special_Guest', '').strip()
            event.other_guests = doc_val.get('Other_Guests', '').strip()
            event.rsvp_info = doc_val.get('RSVP_Info', '').strip()

            # contact
            event.pac_contact = doc_val.get('PAC_Contact', '').strip()
            event.additional_contact = doc_val.get('Additional_Contact', '').strip()

            # money
            event.event_paid_for_by = doc_val.get('Event__Paid_for_By', '').strip()
            event.distribution_paid_for_by = doc_val.get('Distribution_Paid_for_By', '').strip()
            event.make_checks_payable_to = doc_val.get('Make_Checks_Payable_To', '').strip()
            event.checks_payable_to_address = doc_val.get('Checks_Payable_To_Address', '').strip()
            event.contributions_info = doc_val.get('Contributions_Info', '').strip()

            # data entry
            event.user_initials = doc_val.get('USER_INITIALS', '').strip()
            event.data_entry_problems = doc_val.get('Data_Entry_Problems', '').strip()
        
            event.save()

            #
            # beneficiary
            #
        
            Beneficiary.objects.filter(event=event).delete()

            for beneficiary in doc_val.get('Beneficiary', []):
                
                moc = parse_moc(beneficiary)
                
                if moc:

                    b = Beneficiary()
                    b.name = moc.get('name','')
                    b.party = moc.get('party','')[:1]
                    b.state = moc.get('state','')[:2]
                    b.district = moc.get('district','')
                    b.other_info = moc.get('other_info','')
                    b.event = event
                    b.save()

            #
            # host
            #
        
            Host.objects.filter(event=event).delete()
        
            for host in doc_val.get('Host', []):
            
                if host:

                    h = Host()
                    h.name = host.rstrip(';')
                    h.party = ''
                    h.state = ''
                    h.district = ''
                    h.other_info = ''
                    h.event = event
                    h.save()

            #
            # other members
            #
        
            OtherMember.objects.filter(event=event).delete()

            for other_member in doc_val.get('Other_Members_of_Congress', []):
                
                moc = parse_moc(other_member)
                
                if moc:

                    om = OtherMember()
                    om.name = moc.get('name','')
                    om.party = moc.get('party','')[:1]
                    om.state = moc.get('state','')[:2]
                    om.district = moc.get('district','')
                    om.other_info = moc.get('other_info','')
                    om.event = event
                    om.save()
