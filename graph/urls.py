from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('',
    (r'(\d+)/node/(\d+)/(\d+)/$', 'graph.views.node_info'),
    (r'(\d+)/node/(-?\d+)/$', 'graph.views.node_info'),
    (r'(\d+)/node/(\d+)/visualize/$', 'graph.views.visualize'),
    (r'(\d+)/node/expand_node/$', 'graph.views.expand_node'),
    (r'(\d+)/node/open_node_info/$', 'graph.views.open_node_info'),
    (r'(\d+)/node/(\d+)/add_property/$',
        'graph.views.node_property',
        {'action': 'add'}),
    (r'(\d+)/node/(\d+)/modify_property/$',
        'graph.views.node_property',
        {'action': 'modify'}),
    (r'(\d+)/node/(\d+)/delete_property/$',
        'graph.views.node_property',
        {'action': 'delete'}),
    (r'(\d+)/node/(\d+)/add_media/$', 'graph.views.add_media'),
    (r'(\d+)/node/(\d+)/add_media_link/$', 'graph.views.add_media_link'),
    (r'(\d+)/node/(\d+)/create_raw_relationship/$',
        'graph.views.create_raw_relationship'),
    (r'(\d+)/node/(\d+)/delete_node/$', 'graph.views.delete_node'),
    (r'(\d+)/node/(\d+)/delete_relationship/(\d+)/(\d+)/$',
        'graph.views.delete_relationship'),
    (r'(\d+)/relation/(\d+)/([\w-]+)/(\d+)/$', 'graph.views.relation_info'),
    (r'(\d+)/relation/(\d+)/(\w+)/(\d+)/add_property/$',
        'graph.views.relation_property',
        {'action':'add'}),
    (r'(\d+)/relation/(\d+)/(\w+)/(\d+)/modify_property/$',
        'graph.views.relation_property',
        {'action': 'modify'}),
    (r'(\d+)/relation/(\d+)/(\w+)/(\d+)/delete_property/$',
        'graph.views.relation_property',
        {'action': 'delete'}),
    (r'(\d+)/search_nodes_by_field/(\w+)/(\w+)/$', 'graph.views.search_nodes_by_field'),
    (r'(\d+)/get_autocompletion_objects/$', 'graph.views.get_autocompletion_objects'),
    (r'(\d+)/search_node/$', 'graph.views.search_node'),
    (r'^$', 'graph.views.index'),
    (r'(\d+)/$', 'graph.views.editor'),
    (r'(\d+)/search_results/$', 'graph.views.search_results'),
    (r'(\d+)/import_manager/$', 'graph.views.import_manager'),
    (r'(\d+)/add_node_ajax/$', 'graph.views.add_node_ajax'),
    (r'(\d+)/add_relationship_ajax/$', 'graph.views.add_relationship_ajax'),
    (r'(\d+)/visualize_all/$', 'graph.views.visualize_all'),
    (r'export_to_gexf/(.+)/$', 'graph.views.export_to_gexf'),
)
