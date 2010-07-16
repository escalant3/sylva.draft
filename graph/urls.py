from django.conf.urls.defaults import patterns

urlpatterns = patterns('',
    (r'(\d+)/node/(\d+)/$', 'graph.views.node_info'),
    (r'(\d+)/relation/(\d+)/$', 'graph.views.relation_info'),
    (r'(\d+)/$', 'graph.views.editor'),
    (r'(\d+)/(\d+)/add_property/$', 'graph.views.add_property'),
    (r'(\d+)/(\d+)/modify_property/$', 'graph.views.modify_property'),
    (r'(\d+)/(\d+)/delete_property/$', 'graph.views.delete_property'),
    (r'(\d+)/(\d+)/delete_node/$', 'graph.views.delete_node'),
    (r'(\d+)/search_node/$', 'graph.views.search_node'),
    (r'^$', 'graph.views.index'),
)
