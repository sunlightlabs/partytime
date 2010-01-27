from django.conf.urls.defaults import *
from django.contrib import admin
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
    (r'^$', 'partytime.publicsite.views.index'),
    (r'^search/(?P<field>\w+)/(?P<args>.+)/$', 'partytime.publicsite.views.search'),
    (r'^search_embed/(?P<field>\w+)/(?P<args>.+)/$', 'partytime.publicsite.views.search_embed'),
    (r'^search_embed_flex/(?P<field>\w+)/(?P<args>.+)/$', 'partytime.publicsite.views.search_embed_flex'),
    (r'^upcoming_embed/$', 'partytime.publicsite.views.upcoming_embed'),
    (r'^upcoming_embed2/$', 'partytime.publicsite.views.upcoming_embed2'),    
    (r'^search/$', 'partytime.publicsite.views.search_proxy'),
    (r'^recent/$', 'partytime.publicsite.views.recent'),
    (r'^upcoming/$', 'partytime.publicsite.views.upcoming'),
    (r'^bydate/(?P<start>\d{8})/(?P<end>\d{8})/$', 'partytime.publicsite.views.bydate'),
    (r'^upload/thanks/$', 'partytime.publicsite.views.upload_thanks'),
    (r'^upload/$', 'partytime.publicsite.views.upload'),
    (r'^party/(?P<docid>\d+)/$', 'partytime.publicsite.views.party'),
    (r'^contact/', include('contact_form.urls'), {"form_class": PartyTimeContactForm, "fail_silently": False}),
    (r'^accounts/login/$', 'django.contrib.auth.views.login'),
    (r'^admin/', include(admin.site.urls)), 
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
    (r'^pol/(?P<cid>.+)/$', 'partytime.publicsite.views.polwithpac'),
    (r'^leadpacs/$', 'partytime.publicsite.views.leadpac_all'),
    (r'^ical/$', IcalFeed()),
    (r'^accounts/login/$', 'django.contrib.auth.views.login'),
    (r'^accounts/uploadzip/$', 'partytime.publicsite.views.admin_uploadzip'),
    (r'^accounts/replacevenue/(?P<original>\d+)$', 'partytime.publicsite.views.admin_mergevenue'),
    (r'^accounts/replacevenue/(?P<original>\d+)/(?P<replacement>\d+)/$', 'partytime.publicsite.views.admin_mergevenue_confirmed'),
    (r'^accounts/replacelm/(?P<original>\d+)$', 'partytime.publicsite.views.admin_mergelm'),
    (r'^accounts/replacelm/(?P<original>\d+)/(?P<replacement>\d+)/$', 'partytime.publicsite.views.admin_mergelm_confirmed'),
    (r'^lobby/ind/(?P<category>.{5})/$', 'partytime.publicsite.views.lobbydetail'),
    (r'^lobby/corp/(?P<name>.*)/$', 'partytime.publicsite.views.lobbydetailcorp'),
    (r'^lobby/(?P<level>.*)/$', 'partytime.publicsite.views.lobby'),
    (r'^ajax/checkfordupes/$', 'partytime.publicsite.views.admin_checkfordupes'),
    (r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': '/home/luke/partytime/partytime/media/' }),
    (r'^json/(?P<CID>.+)/', 'partytime.publicsite.views.jsonCID')
)





