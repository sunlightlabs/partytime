from django.core.management.base import BaseCommand, CommandError
from api.report import submit_report
from django.conf import settings
from urlparse import urljoin
import datetime


#LOG_PATH = getattr(settings, 'LOCKSMITH_LOG_PATH', '/var/log/nginx/access.log')


LOG_DATE_FORMAT = getattr(settings, 'LOCKSMITH_DATE_FORMAT', '%d/%b/%Y')
LOG_PATH = getattr(settings, 'LOG_PATH')

class Command(BaseCommand):
    help = "Push a given day's logs to the analytics hub by parsing webserver logs."
    args = '[date:YYYY-MM-DD]'
    requires_model_validation = False
    
    def handle(self, date=None, *args, **options):
        if date:
            parsed_date = datetime.datetime.strptime(date, '%Y-%m-%d').date()
        else:
            parsed_date = (datetime.datetime.now() - datetime.timedelta(days=1)).date()
        
        print 'pushing logs for %s' % parsed_date.strftime('%Y-%m-%d')
        
        total_submitted = submit_report(
            log_path = LOG_PATH,
            log_date_format = LOG_DATE_FORMAT,
            log_date = parsed_date,
            locksmith_api_name = settings.LOCKSMITH_API_NAME,
            locksmith_signing_key = settings.LOCKSMITH_SIGNING_KEY,
            locksmith_endpoint = urljoin(settings.LOCKSMITH_HUB_URL, 'report_calls/')
        )
        
        print 'submitted %s hits' % total_submitted
