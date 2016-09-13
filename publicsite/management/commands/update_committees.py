"""Find the chairmen, ranking members and other members of House and Senate committees.
"""
import re

from django.core.management.base import NoArgsCommand
from django.db.models import Q

from publicsite.models import Lawmaker, Committee, CommitteeMembership

from votesmart import votesmart

# TODO: don't hardcode the api key!
votesmart.apikey = '***REMOVED***'


class Command(NoArgsCommand):

    help = "Import committee membership from the Vote Smart API."
    requires_model_validation  = False

    def handle_noargs(self, **options):

        committees = votesmart.committee.getCommitteesByTypeState(typeId=None, stateId='NA')

        for committee in committees:

            # Skip subcommittees for now.
            if committee.name.find('Subcommittee') > -1:
                #print body, committee.name
                continue

            body = {'H': 'House', 'J': 'Joint', 'S': 'Senate'}[committee.committeetypeId]

            if body is not 'Joint':
                if (committee.name.startswith('Special') or 
                        committee.name.startswith('Permanent') or
                        committee.name.startswith('Select')
                        ):
                    fullname = '%s %s' % (body, committee.name)
                else:
                    fullname = '%s Committee on %s' % (body, committee.name)
            else:
                fullname = committee.name

            fullname = fullname.replace('on Budget', 'on the Budget').replace('on Judiciary', 'on the Judiciary')

            try:
                pt_committee = Committee.objects.get(title=fullname)

            except Committee.DoesNotExist:
                # Add serial comma; some committee names need it.
                fullname = re.sub(r'(\w) and ', r'\1, and ', fullname)
                try:
                    pt_committee = Committee.objects.get(title=fullname)

                except Committee.DoesNotExist:
                    continue


            id = committee.committeeId
            members = votesmart.committee.getCommitteeMembers(id)

            for member in members:
                bio = votesmart.candidatebio.getBio(member.candidateId)
                crp_id = bio.crpId

                if not crp_id:
                    continue

                pt_member = Lawmaker.objects.filter(Q(affiliate='') | Q(affiliate__isnull=True), crp_id=crp_id)
                if not pt_member:
                    continue

                pt_member = pt_member[0]

                membership = CommitteeMembership(committee=pt_committee,
                                                 member=pt_member,
                                                 position=member.position)
                membership.save()

                print pt_committee, pt_member, member.position, membership

            print
