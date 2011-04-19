import datetime

from django.template import defaultfilters

from graph.models import Node
from schema.models import NodeType


def create_node(gdb, n, graph):
    original_id = n['_slug']
    n['_slug'] = defaultfilters.slugify(n['_slug'])[:150]
    node_properties = {}
    if original_id != n['_slug']:
        node_properties['id'] = original_id
    node_type_obj = NodeType.objects.filter(name=n['_type'])
    if node_type_obj:
        default_properties = node_type_obj[0].nodeproperty_set.all()
        for dp in default_properties:
            node_properties[dp.key] = dp.value
    for key, value in n.items():
        node_properties[key] = value
    result = search_in_index(gdb, n['_slug'], n['_type'], n['_graph'])
    if result:
        counter = 1
        slug = "%s-%s" % (n['_slug'], counter)
        result = search_in_index(gdb, slug, n['_type'], n['_graph'])
        while result:
            counter += 1
            slug = "%s-%s" % (n['_slug'], counter)
            result = search_in_index(gdb, slug, n['_type'], n['_graph'])
        node_properties['_slug'] = slug
    node = gdb.node(**node_properties)
    node.set('_url', "/".join(node.url.split('/')[-2:]))
    idx = gdb.nodes.indexes.get('sylva_nodes')
    idx['_slug'][node['_slug']] = node
    idx['_type'][node['_type']] = node

 
    idx['_graph'][node['_graph']] = node
    sql_node = Node(graph=graph,
                            node_id=node['_slug'],
                            node_type=node['_type'])
    sql_node.save()
    graph.node_set.add(sql_node)
    return node


def search_in_index(gdb, _slug, _type, _graph):
    idx = gdb.nodes.indexes.get('sylva_nodes')
    result = filter_by_property(idx.get('_slug')[_slug],
                                '_type', _type)
    result = filter_by_property(result, '_graph', _graph)
    return result


def filter_by_property(nodes, prop, value):
    return [n for n in nodes if n.properties[prop] == value]


def get_internal_attributes(slug, _type, graph_id, user, relation=False):
    internal_attrs = {'_slug': slug,
            '_type': _type,
            '_graph': graph_id,
            #'_user': user.username,
            '_timestamp': get_timestamp(),
            '_origin': 1,
            }
    if relation:
        internal_attrs['_weight'] = False
    return internal_attrs


def get_timestamp():
    timestamp = datetime.datetime.now()
    return timestamp.strftime('%Y-%m-%d %H:%M:%S')


def update_timestamp(element, username):
    element.set('_timestamp', get_timestamp())
    element.set('_user', username)

