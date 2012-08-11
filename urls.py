import time

from django.conf.urls.defaults import *
from django.contrib import admin
from django.views.decorators.cache import cache_page

from publicsite.feeds import *
from settings import *

from contact_form.forms import ContactForm

class PartyTimeContactForm(ContactForm):
    from_email = "partytime@sunlightfoundation.com"
    recipient_list = ["partytime@sunlightfoundation.com"]
    subject = "[PoliticalPartyTime.org] Contact"

feeds = {
    'recent': RecentFeed,
    'upcoming': UpcomingFeed,
    'pol': PolFeed,
    'newlyadded':NewFeed,
    'presidential':PresidentFeed,
}
# need to add presidential to feeds

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'partytime.publicsite.views.index', name='partytime_home'),
    url(r'^', include('mediasync.urls')),
    url(r'^blog/', include('wordpress.urls')),
    # there didn't use to *be* a blog home page -- it was instead the home page. 
    url(r'^blogindex/$', 'partytime.publicsite.views.blogindex', name='blogindex'),
    
    # flattish nav pages
    url(r'^about/$', 'django.views.generic.simple.direct_to_template', {'template': 'publicsite_redesign/about.html'}),
    url(r'^FAQ/$', 'django.views.generic.simple.direct_to_template', {'template': 'publicsite_redesign/FAQ.html'}),
    url(r'^api/$', 'django.views.generic.simple.direct_to_template', {'template': 'publicsite_redesign/api.html'}),
    url(r'^upload/$', 'partytime.publicsite.views.upload', name='partytime_upload'),
    url(r'^contact/', include('contact_form.urls'), {"form_class": PartyTimeContactForm, "fail_silently": False}, name='partytime_contact'),
    
    # results pages linked to from the home page
    url(r'^recent/$', 'partytime.publicsite.views.recent', name='partytime_recent'),    
    url(r'^upcoming/$', 'partytime.publicsite.views.upcoming', name='partytime_upcoming'), 
    url(r'^newly-added/$', 'partytime.publicsite.views.newly_added', name='partytime_newly_added'),            
    url(r'^committee-leadership/$', 'partytime.publicsite.views.committee_leadership', name='partytime_committee_leadership'),
    url(r'^congressional-leadership/$', 'partytime.publicsite.views.congressional_leadership', name='partytime_congressional_leadership'),    
    url(r'^hosted-by-congressional-leadership/$', 'partytime.publicsite.views.hosted_by_congressional_leadership', name='partytime_hosted_by_congressional_leadership'),
    url(r'^presidential/$', 'partytime.publicsite.views.presidential', name='partytime_presidential'),
    
    
    
    
    
    ### End redesigned views:
    
    url(r'^search/(?P<field>\w+)/(?P<args>.+)/$', 'partytime.publicsite.views.search', name='partytime_search'),
    url(r'^search_embed/(?P<field>\w+)/(?P<args>.+)/$', 'partytime.publicsite.views.search_embed', name='partytime_search_embed'),
    url(r'^search_embed_flex/(?P<field>\w+)/(?P<args>.+)/$', 'partytime.publicsite.views.search_embed_flex', name='partytime_search_embed_flex'),
    url(r'^upcoming_embed/$', 'partytime.publicsite.views.upcoming_embed', name='partytime_upcoming_embed'),
    url(r'^upcoming_embed2/$', 'partytime.publicsite.views.upcoming_embed2', name='partytime_upcoming_embed2'),
    url(r'^search/$', 'partytime.publicsite.views.search_proxy', name='partytime_search_proxy'),

    url(r'^bydate/(?P<start>\d{8})/(?P<end>\d{8})/$', 'partytime.publicsite.views.bydate', name='partytime_bydate'),
    url(r'^upload/thanks/$', 'partytime.publicsite.views.upload_thanks', name='partytime_uploadthanks'),
    url(r'^party/(?P<docid>\d+)/$', 'partytime.publicsite.views.party', name='partytime_party_detail'),
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
    url(r'^supercommittee/$', 'partytime.publicsite.views.supercommittee', name='partytime_supercommittee'),
    url(r'^committee/(?P<chamber>\w*)/$', 'partytime.publicsite.views.cmtes', name='partytime_chamber_committees'),
    url(r'^committee/update/(?P<chamber>\w*)/$', 'partytime.publicsite.views.updatecmtes'),   #temp
    url(r'^committee/$', 'partytime.publicsite.views.cmtes', {'chamber': 'House'}, name='partytime_committee_list'),

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
#    url(r'^layar/$', 'partytime.publicsite.views.partytime_layar', name='partytime_layar'),
    url(r'^emailalerts/', 'partytime.publicsite.views.email_subscribe'),
#    url(r'^townhouses/layar/$', 'partytime.publicsite.views.townhouse_layar', name='partytime_townhouse_layar'),
    url(r'^townhouses/', 'django.views.generic.simple.direct_to_template', {'template': 'publicsite/townhouses.html', 'extra_context': {'timestamp': str(int(time.time())), }, }),
    url(r'^venue/(?P<venue_id>\d+)/$', 'partytime.publicsite.views.venue_detail', name='partytime_venue_detail'),
    
    ## for redesign testing
    url(r'^new_base/$', 'django.views.generic.simple.direct_to_template', {'template': 'publicsite_redesign/base.html', 'extra_context': {'filler': 'this is some filler', }, }),
    url(r'^templatetagtest/$', 'django.views.generic.simple.direct_to_template', {'template': 'publicsite_redesign/templatetagtest.html'}),
    url(r'^indextest/$', 'partytime.publicsite.views.index'),
    url(r'^about_test/$', 'django.views.generic.simple.direct_to_template', {'template': 'publicsite_redesign/abouttest.html'})
    
)

urlpatterns += patterns('django.views.generic.simple',
    url(r'^data/all/$', 'direct_to_template', {'template': 'publicsite/data_page.html'}),
)

from sitemap import sitemaps

urlpatterns += patterns('',
    (r'^sitemap\.xml$', 'django.contrib.sitemaps.views.index', {'sitemaps': sitemaps}),
    (r'^sitemap-(?P<section>.+)\.xml$', 'django.contrib.sitemaps.views.sitemap', {'sitemaps': sitemaps})
)
