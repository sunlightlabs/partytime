from tastypie.authentication import Authentication
from locksmith.auth.models import ApiKey


class LocksmithKeyAuthentication(Authentication):
    def is_authenticated(self, request, **kwargs):
        return hasattr(request, 'apikey') and request.apikey.status == 'A'

    # Optional but recommended
    def get_identifier(self, request):
        return request.apikey