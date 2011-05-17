from django.conf.urls.defaults import patterns, url
from django.views.generic.create_update import delete_object

from schema.models import NodeProperty

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
    (r'edit_graph/(\d+)/$', 'schema.views.edit_graph'),
    (r'edit_permissions/(\d+)/$', 'schema.views.edit_graph_permissions'),
    (r'(\d+)/$', 'schema.views.schema_editor'),
    (r'add_graph/$', 'schema.views.add_graph'),

    # Add valid relationship
    url(r'(\d+)/nodetype/(\d+)/relation/add/$',
        'schema.views.schema_relation_add', name="schema_relation_add"),

    # Edit node type
    url(r'(\d+)/nodetype/(\d+)/property/(\d+)/edit/$',
        'schema.views.schema_property_edit', name="schema_property_edit"),

    # Delete node type
    url(r'(\d+)/nodetype/(\d+)/property/(?P<object_id>[0-9]+)/delete/$',
        delete_object,
        {'model': NodeProperty,
         'post_delete_redirect': '../../../',
         'template_name': "graphgamel/graph_manager/delete_ndp.html"},
        name="schema_property_delete"),

)
