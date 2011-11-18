from django.core.management.base import BaseCommand

from publicsite.models import Lawmaker, SuperCommitteeMember

class Command(BaseCommand):

    def handle(self, *args, **options):
        names = ['patty murray',
                 'max baucus',
                 'john kerry',
                 'jon kyl',
                 'pat toomey',
                 'rob portman',
                 'jim clyburn',
                 'xavier becerra',
                 'chris van hollen',
                 'jeb hensarling',
                 'david camp',
                 'fred upton', ]

        for name in names:
            lawmaker = Lawmaker.objects.get(name=name)
            member = SuperCommitteeMember.objects.create(lawmaker=lawmaker)
            print member
