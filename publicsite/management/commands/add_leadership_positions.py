from django.core.management.base import NoArgsCommand
from django.db.models import Q

from publicsite.models import Lawmaker, LeadershipPosition

from sunlightapi import sunlight
sunlight.apikey = '***REMOVED***'


class Command(NoArgsCommand):

    help = 'Add leadership positions to the database.'
    requires_model_validation = False

    def handle_noargs(self, **options):
        leadership = """
S,President of the Senate,Joseph R. Biden Jr.,
S,President pro tempore,Daniel K. Inouye,D-HI
S,Senate majority leader,Harry Reid,D-NV
S,Senate majority whip,Richard Durbin,D-IL
S,Senate minority leader,Mitch McConnell,R-KY
S,Senate minority whip,Jon Kyl,R-AZ
H,Speaker of the house,Nancy Pelosi,D-CA
H,House majority leader,Steny Hoyer,D-MD
H,House minority leader,John Boehner,R-OH
H,House majority whip,James E. Clyburn,D-SC
H,House minority whip,Eric Cantor,R-VA
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
