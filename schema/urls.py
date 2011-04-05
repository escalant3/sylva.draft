from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('',
    (r'(\d+)/add_node_type/$', 'schema.views.add_node_type'),
    (r'(\d+)/add_edge_type/$', 'schema.views.add_edge_type'),
    (r'(\d+)/add_valid_relationship/$', 'schema.views.add_valid_relationship'),
    (r'(\d+)/$', 'schema.views.schema_editor'),
    (r'add_graph/$', 'schema.views.add_graph'),
)
