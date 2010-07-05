from django.conf.urls.defaults import patterns

urlpatterns = patterns('',
    (r'(\d+)/(\d+)/$', 'graph.views.info'),
    (r'(\d+)/$', 'graph.views.editor'),
    (r'^$', 'graph.views.index'),
)
