from urllib import urlencode


def get_current_url(request):
    return {
        'current_url': _get_url_from_request(request)
    }


def get_current_url_with_querystring(request):
    qs = urlencode(request.GET)
    if qs:
        qs = '?' + qs
    return {
        'current_url_with_querystring': u"%s%s" % (_get_url_from_request(request),
                                                   qs)
    }


def _get_url_from_request(request):
    path = request.get_full_path()
    domain = request.get_host()
    protocol = "https" if request.is_secure() else "http"
    return u"%s://%s%s" % (protocol, domain, path)
