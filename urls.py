import os

from django.conf.urls.defaults import patterns, include
from django.contrib.auth.views import login, logout

from django.contrib import admin
admin.autodiscover()
site_media = os.path.join(os.path.dirname(__file__), 'site_media')

urlpatterns = patterns('',
    (r'^site_media/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': site_media}),
    (r'^admin/', include(admin.site.urls)),
    (r'^accounts/login/$', login),
    (r'^accounts/logout/$', logout),
    (r'^schema/', include('schema.urls')),
    (r'user_profile/$', 'schema.views.user_profile'),
    (r'^', include('graph.urls')),
)
