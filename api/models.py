from django.db import models

# for analytics. Should really be mongo, but... 
class LogEntry(models.Model):
    method = models.CharField(max_length=1, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now=True)
    caller_key = models.CharField(max_length=32)
    