from django.core.management.base import NoArgsCommand
from django.db.models import Q

from publicsite.models import Lawmaker, LeadershipPosition

from sunlightapi import sunlight
#TODO : don't hardcode the apikey!
sunlight.apikey = '***REMOVED***'


class Command(NoArgsCommand):

    help = 'Add leadership positions to the database.'
    requires_model_validation = False

    def handle_noargs(self, **options):
        leadership = """
S,President of the Senate,Joseph R. Biden Jr.,
S,President pro tempore,Daniel K. Inouye,D-HI
S,Senate majority leader,Harry Reid,D-NV
S,Senate minority leader,Mitch McConnell,R-KY
S,Senate minority whip,Jon Kyl,R-AZ
H,House majority leader,Nancy Pelosi,D-CA
H,House minority whip,Steny Hoyer,D-MD
H,Speaker of the House,John Boehner,R-OH
H,House majority leader,Eric Cantor,R-VA
        """.split('\n')
        leadership = [x.strip().split(',') for x in leadership if x.strip()]

        for lm in leadership:
            body, position, name, affiliation = lm
            legislator = sunlight.legislators.search(name)
            if not legislator:
                print '%s not found' % name
                continue

            legislator = legislator[0].legislator
            lawmaker = Lawmaker.objects.get(Q(affiliate__isnull=True) | Q(affiliate=''), crp_id=legislator.crp_id)

            LeadershipPosition.objects.create(congress='111th',
                                              lawmaker=lawmaker,
                                              position=position,
                                              body=body)
            print LeadershipPosition
