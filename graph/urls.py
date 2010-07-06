from django.conf.urls.defaults import patterns

urlpatterns = patterns('',
    (r'(\d+)/(\d+)/$', 'graph.views.info'),
    (r'(\d+)/$', 'graph.views.editor'),
    (r'(\d+)/(\d+)/add_property/$', 'graph.views.add_property'),
    (r'^$', 'graph.views.index'),
)
