import re

from django.core.management.base import NoArgsCommand
from lxml.html import parse

from publicsite.models import CookRating


def get_latest_url(list_url):
    doc = parse(list_url).getroot()
    return 'http://www.cookpolitical.com%s' % doc.cssselect('h1')[0].getnext().cssselect('a')[0].values()[0]


def get_senate_ratings():
    url = get_latest_url('http://www.cookpolitical.com/node/4060')
    doc = parse(url).getroot()

    good_tds = []

    for td in doc.cssselect('td'):
        d = dict(td.items())
        if not d.has_key('width') or not d['width'] == '92':
            continue
        data = [x for x in list(td.itertext()) if x.strip()]
        if len(data) == 1:
            continue

        rating = re.sub(r' \(.*$', '', data[0]) \
                .lower() \
                .replace(' ', '_') \
                .replace('toss_up', 'tossup') \
                
        data = data[1:]

        for race in data:
            state = re.search(r'[A-Z]{2}', race).group()
            district = ''
            body = 'S'

            cr, created = CookRating.objects.get_or_create(body=body,
                                           state=state,
                                           district=district,
                                           rating=rating)
            cr.save()


def get_house_ratings():
    url = get_latest_url('http://www.cookpolitical.com/node/4056')
    doc = parse(url).getroot()

    tables = doc.cssselect('table.nestedTable')

    data = {}

    (data['likely_dem'],
     data['lean_dem'],
     data['dem_tossup'],
     data['gop_tossup'],
     data['lean_gop'],
     data['likely_gop']) = tables

    candidate_data = {}

    for key in data.keys():
        rows = data[key].cssselect('tr')[1:]
        for row in rows:
            district, incumbent, score = list(row.itertext())[::2]
            rating = key
            state, district = district.split('-')
            body = 'H'

            cr, created = CookRating.objects.get_or_create(body=body,
                                           state=state,
                                           district=district,
                                           rating=rating)
            cr.save()


class Command(NoArgsCommand):

    help = "Gets data on Cook Political Report competitive races."

    requires_model_validation = False

    def handle_noargs(self, **options):
        get_house_ratings()
        get_senate_ratings()
