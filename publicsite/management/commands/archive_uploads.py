from django.conf import settings
from django.core.mail import EmailMessage
from django.core.management.base import NoArgsCommand
from optparse import make_option
import datetime
import os
import zipfile

class Command(NoArgsCommand):
    
    help = "Creates an archive of recently uploaded files"
    
    requires_model_validation = False
    
    def handle_noargs(self, **options):
    
        upload_dir_path = "%s/upload" % settings.FILE_UPLOAD_PATH
        archive_dir_path = "%s/archive" % settings.FILE_UPLOAD_PATH
        
        archive_file = "%s.zip" % datetime.datetime.now().strftime("%Y%m%d%H%M")
        archive_path = "%s/%s" % (archive_dir_path, archive_file)
        
        files = os.listdir(upload_dir_path)
        files = [f for f in files if not f.startswith(".")]
            
        if files:
            
            archived_files = []
            
            # write files to archive

            zf = zipfile.ZipFile(archive_path, "w")
            for f in files:
                zf.write("%s/%s" % (upload_dir_path, f), f, zipfile.ZIP_DEFLATED)    
            zf.close()
        
            # delete files that made it to the archive
        
            zf = zipfile.ZipFile(archive_path, "r")
            for info in zf.infolist():
                os.remove("%s/%s" % (upload_dir_path, info.filename))
                archived_files.append(info.filename)
            zf.close()
            
            # send email
            
            subject = "Uploads from PoliticalPartyTime.org"
            body = "\n".join(archived_files) + "\n\n"
            sender = "partytime@sunlightfoundation.com"
            recipient = ['jruihley@sunlightfoundation.com','jcarbaugh@sunlightfoundation.com', 'timball@sunlightfoundation.com', 'nwatzman@sunlightfoundation.com']
            reply_to = "bounce@sunlightfoundation.com"
            
            attachment = open(archive_path, 'rb').read()
            
            email = EmailMessage(subject, body, sender, recipient, headers={'Reply-To': reply_to})
            email.attach(archive_file, attachment, 'application/zip')
            email.send()
