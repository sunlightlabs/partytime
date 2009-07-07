from django.conf.urls.defaults import *
from django.contrib import admin
from publicsite.feeds import *

from contact_form.forms import ContactForm

class PartyTimeContactForm(ContactForm):
    from_email = "bounce@sunlightfoundation.com"
    recipient_list = ['gschneider@sunlightfoundation.com','nwatzman@sunlightfoundation.com']
    subject = "[PoliticalPartyTime.org] Contact"

feeds = {
    'recent': RecentFeed,
    'upcoming': UpcomingFeed,
}

admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^partytime/', include('partytime.foo.urls')),
    (r'^$', 'partytime.publicsite.views.index'),
    (r'^search/(?P<field>\w+)/(?P<args>.+)/$', 'partytime.publicsite.views.search'),
    (r'^search_embed/(?P<field>\w+)/(?P<args>.+)/$', 'partytime.publicsite.views.search_embed'),
    (r'^search/$', 'partytime.publicsite.views.search_proxy'),
    (r'^recent/$', 'partytime.publicsite.views.recent'),
    (r'^upcoming/$', 'partytime.publicsite.views.upcoming'),
    (r'^bydate/(?P<start>\d{8})/(?P<end>\d{8})/$', 'partytime.publicsite.views.bydate'),
    (r'^upload/thanks/$', 'partytime.publicsite.views.upload_thanks'),
    (r'^upload/$', 'partytime.publicsite.views.upload'),
    (r'^party/(?P<docid>\d+)/$', 'partytime.publicsite.views.party'),
    (r'^contact/', include('contact_form.urls'), {"form_class": PartyTimeContactForm, "fail_silently": False}),
    (r'^accounts/login/$', 'django.contrib.auth.views.login'),
    (r'^admin/(.*)', admin.site.root),
    (r'^feeds/(?P<url>.*)/$', 'django.contrib.syndication.views.feed', {'feed_dict': feeds}),
    (r'^convention/(?P<convention>\w+)/$', 'partytime.publicsite.views.convention_list'),
    (r'^convention/$', 'partytime.publicsite.views.convention_list'),
    (r'^widget/abc_convention/(?P<convention>\w+)/$', 'partytime.publicsite.views.abc_convention'),
    (r'^widget/abc_convention/$', 'partytime.publicsite.views.abc_convention'),
    (r'^widget/widget_180/$', 'partytime.publicsite.views.widget180_upcoming'),
    (r'^widget/leadpacs/$', 'partytime.publicsite.views.leadpacs'),
    (r'^committee/(?P<cmteid>\w{4})/$', 'partytime.publicsite.views.cmtedetail' ),
    (r'^committee/(?P<chamber>\w*)/$', 'partytime.publicsite.views.cmtes'),
    (r'^committee/update/(?P<chamber>\w*)/$', 'partytime.publicsite.views.updatecmtes'),   #temp
    (r'^committee/$', 'partytime.publicsite.views.cmtes', {'chamber': 'House'} ),
    (r'^dump/all$', 'partytime.publicsite.views.dump_all'),
    (r'^dump/mult$', 'partytime.publicsite.views.dump_mult'),
    (r'^ical/$', IcalFeed())
)
