from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('',
    (r'(\d+)/add_node_type/$', 'schema.views.add_node_type'),
    (r'(\d+)/add_edge_type/$', 'schema.views.add_edge_type'),
    (r'(\d+)/(\d+)/add_default_node_property/$',
        'schema.views.add_default_node_property'),
    (r'(\d+)/(\d+)/add_default_edge_property/$',
        'schema.views.add_default_edge_property'),
    (r'(\d+)/(\d+)/delete_default_node_property/$',
        'schema.views.delete_default_node_property'),
    (r'(\d+)/(\d+)/add_delete_edge_property/$',
        'schema.views.delete_default_edge_property'),
    (r'(\d+)/add_valid_relationship/$',
        'schema.views.add_valid_relationship'),
    (r'delete_graph/(\d+)/$', 'schema.views.delete_graph'),
    (r'(\d+)/$', 'schema.views.schema_editor'),
    (r'add_graph/$', 'schema.views.add_graph'),
)
