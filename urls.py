from django.conf.urls.defaults import *
from django.contrib import admin
from django.views.decorators.cache import cache_page

from publicsite.feeds import *
from settings import *

from contact_form.forms import ContactForm

class PartyTimeContactForm(ContactForm):
    from_email = "bounce@sunlightfoundation.com"
    recipient_list = ['gschneider@sunlightfoundation.com','nwatzman@sunlightfoundation.com']
    subject = "[PoliticalPartyTime.org] Contact"

feeds = {
    'recent': RecentFeed,
    'upcoming': UpcomingFeed,
    'pol': PolFeed
}

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'partytime.publicsite.views.index', name='partytime_home'),
    url(r'^search/(?P<field>\w+)/(?P<args>.+)/$', 'partytime.publicsite.views.search', name='partytime_search'),
    url(r'^search_embed/(?P<field>\w+)/(?P<args>.+)/$', 'partytime.publicsite.views.search_embed', name='partytime_search_embed'),
    url(r'^search_embed_flex/(?P<field>\w+)/(?P<args>.+)/$', 'partytime.publicsite.views.search_embed_flex', name='partytime_search_embed_flex'),
    url(r'^upcoming_embed/$', 'partytime.publicsite.views.upcoming_embed', name='partytime_upcoming_embed'),
    url(r'^upcoming_embed2/$', 'partytime.publicsite.views.upcoming_embed2', name='partytime_upcoming_embed2'),
    url(r'^search/$', 'partytime.publicsite.views.search_proxy', name='partytime_search_proxy'),
    url(r'^recent/$', 'partytime.publicsite.views.recent', name='partytime_recent'),
    url(r'^upcoming/$', 'partytime.publicsite.views.upcoming', name='partytime_upcoming'),
    url(r'^bydate/(?P<start>\d{8})/(?P<end>\d{8})/$', 'partytime.publicsite.views.bydate', name='partytime_bydate'),
    url(r'^upload/thanks/$', 'partytime.publicsite.views.upload_thanks', name='partytime_uploadthanks'),
    url(r'^upload/$', 'partytime.publicsite.views.upload', name='partytime_upload'),
    url(r'^party/(?P<docid>\d+)/$', 'partytime.publicsite.views.party', name='partytime_party_detail'),
    url(r'^contact/', include('contact_form.urls'), {"form_class": PartyTimeContactForm, "fail_silently": False}, name='partytime_contact'),
    url(r'^accounts/login/$', 'django.contrib.auth.views.login'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^feeds/(?P<url>.*)/$', 'django.contrib.syndication.views.feed', {'feed_dict': feeds}, name='partytime_feeds'),
    url(r'^convention/(?P<convention>\w+)/$', 'partytime.publicsite.views.convention_list', name='partytime_convention_detail'),
    url(r'^convention/$', 'partytime.publicsite.views.convention_list', name='partytime_convention_events'),
    url(r'^widget/abc_convention/(?P<convention>\w+)/$', 'partytime.publicsite.views.abc_convention', name='partytime_abc_convention_detail'),
    url(r'^widget/abc_convention/$', 'partytime.publicsite.views.abc_convention', name='partytime_abc_convention'),
    url(r'^widget/widget_180/$', 'partytime.publicsite.views.widget180_upcoming', name='partytime_widget_180'),
    url(r'^widget/leadpacs/$', 'partytime.publicsite.views.leadpacs', name='partytime_leadpacs'),
    url(r'^widget/(?P<state>\w{2})/$', 'partytime.publicsite.views.widget_state', name='partytime_widget_state'),
    url(r'^committee/(?P<cmteid>\w{4})/$', 'partytime.publicsite.views.cmtedetail', name='partytime_committee_detail'),
    url(r'^committee/(?P<chamber>\w*)/$', 'partytime.publicsite.views.cmtes', name='partytime_chamber_committees'),
    url(r'^committee/update/(?P<chamber>\w*)/$', 'partytime.publicsite.views.updatecmtes'),   #temp
    url(r'^committee/$', 'partytime.publicsite.views.cmtes', {'chamber': 'House'}, name='partytime_committee_list'),
    url(r'^committee-leadership/$', 'partytime.publicsite.views.committee_leadership', name='partytime_committee_leadership'),
    url(r'^congressional-leadership/$', 'partytime.publicsite.views.congressional_leadership', name='partytime_congressional_leadership'),
    url(r'^pol/(?P<cid>.+)/$', 'partytime.publicsite.views.polwithpac', name='partytime_pol_detail'),
    url(r'^leadpacs/$', 'partytime.publicsite.views.leadpac_all', name='partytime_leadpacs'),
    url(r'^ical/$', IcalFeed(), name='partytime_ical'),
    url(r'^accounts/login/$', 'django.contrib.auth.views.login'),
    url(r'^accounts/uploadzip/$', 'partytime.publicsite.views.admin_uploadzip'),
    url(r'^accounts/replacevenue/(?P<original>\d+)$', 'partytime.publicsite.views.admin_mergevenue'),
    url(r'^accounts/replacevenue/(?P<original>\d+)/(?P<replacement>\d+)/$', 'partytime.publicsite.views.admin_mergevenue_confirmed'),
    url(r'^accounts/replacelm/(?P<original>\d+)$', 'partytime.publicsite.views.admin_mergelm'),
    url(r'^accounts/replacelm/(?P<original>\d+)/(?P<replacement>\d+)/$', 'partytime.publicsite.views.admin_mergelm_confirmed'),
    url(r'^ajax/checkfordupes/$', 'partytime.publicsite.views.admin_checkfordupes'),
    url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': '/home/luke/partytime/partytime/media/' }),
    url(r'^json/(?P<CID>.+)/', 'partytime.publicsite.views.jsonCID'),
    url(r'^layar/$', 'partytime.publicsite.views.partytime_layar', name='partytime_layar'),
    url(r'^emailalerts/', 'partytime.publicsite.views.email_subscribe'),
)

urlpatterns += patterns('django.views.generic.simple',
    url(r'^data/all/$', 'direct_to_template', {'template': 'publicsite/data_page.html'}),
)
