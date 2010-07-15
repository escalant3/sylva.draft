import neo4jclient
import simplejson

from django.shortcuts import render_to_response, redirect, HttpResponse

from graph.models import Graph


RESERVED_FIELD_NAMES = ('id', 'type')


def index(request):
    graphs = Graph.objects.all()
    messages = request.session.get('messages', None)
    return render_to_response('graphgamel/index.html', {
                        'graph_list': graphs,
                        'messages': messages})


def return_function(obj, value, show_info):
    if show_info:
        return obj, value
    else:
        return obj


def get_or_create_node(gdb, n, creation_info=False):
    created = False
    result = filter_by_property(gdb.index('id', n['id']),
                                'type', n['type'])
    if len(result) == 1:
        node = result[0]
        for key, value in n.iteritems():
            node.set(key, value)
    else:
        node = gdb.node(**n)
        gdb.add_to_index('id', n['id'], node)
        gdb.add_to_index('type', n['type'], node)
        created = True
    return return_function(node, created, creation_info)


def get_or_create_relationship(node1, node2, edge_type, creation_info=False):
    created = True
    for relation in node1.relationships.all():
        if relation.end == node2:
            created = False
            break
    else:
        relation = getattr(node1, edge_type)(node2)
    return return_function(relation, created, creation_info)


def editor(request, graph_id):
    messages = []
    graph = Graph.objects.get(pk=graph_id)
    schema = graph.schema
    if request.method == 'POST':
        gdb = neo4jclient.GraphDatabase(request.session['host'])
        if gdb:
            data = request.POST.copy()
            if data['mode'] == 'node':
                n = {'id': data['node_id'], 'type': data['node_type']}
                properties = simplejson.loads(data['node_properties'])
                n.update(properties)
                node, new = get_or_create_node(gdb, n, True)
                if new:
                    messages = ['Created %s' % (data['node_id'])]
                else:
                    messages = ['Node %s already exists' % n['id']]
            elif data['mode'] == 'relation':
                #Check if it is a valid relationship
                #Create data in Neo4j server
                node_from = {'id': data['node_from_id'],
                            'type': data['node_from_type']}
                properties = simplejson.loads(data['node_from_properties'])
                node_from.update(properties)
                relation = {'type': data['relation_type']}
                properties = simplejson.loads(data['relation_properties'])
                relation.update(properties)
                node_to = {'id': data['node_to_id'],
                            'type': data['node_to_type']}
                properties = simplejson.loads(data['node_to_properties'])
                node_to.update(properties)
                edge_type = relation['type']
                node1 = get_or_create_node(gdb, node_from)
                node2 = get_or_create_node(gdb, node_to)
                rel_obj, new = get_or_create_relationship(node1,
                                                            node2,
                                                            edge_type,
                                                            True)
                for key, value in relation.iteritems():
                    rel_obj.set(key, value)
                if new:
                    action = 'Created'
                else:
                    action = 'Modified'
                messages = ['%s %s(%s) %s %s(%s) relation' %
                                        (action,
                                        data['node_from_id'],
                                        data['node_from_type'],
                                        edge_type,
                                        data['node_to_id'],
                                        data['node_to_type'])]
    else:
        # Check connection
        host = graph.neo4jgraph.host
        try:
            gdb = neo4jclient.GraphDatabase(host)
            request.session["host"] = host
            messages = ['Successfully connected to %s' % host]
        except:
            request.session['messages'] = ['Unavailable host']
            return redirect(index)
        form_structure = simplejson.dumps(schema.get_dictionaries())
        node_types = simplejson.dumps(schema.get_node_types())
        request.session['form_structure'] = form_structure
        request.session['node_types'] = node_types
    form_structure = request.session['form_structure']
    node_types = request.session['node_types']
    return render_to_response('graphgamel/editor.html', {
                        'schema': schema,
                        'messages': messages,
                        'form_structure': form_structure,
                        'node_types': node_types})


def info(request, graph_id, node_id):
    gdb = neo4jclient.GraphDatabase(request.session["host"])
    node = gdb.node[int(node_id)]
    properties = simplejson.dumps(node.properties)
    relationships = node.relationships.all()
    relationships_list = []
    for r in relationships:
        relation_info = {'start_id': r.start.get('id', None),
                        'start_type': r.start.get('type', None),
                        'start_url': r.start.url,
                        'relation_type': r.type,
                        'relation_url': r.url,
                        'end_id': r.end.get('id', None),
                        'end_type': r.end.get('type', None),
                        'end_url': r.end.url}
        relationships_list.append(relation_info)
    graph = Graph.objects.get(pk=graph_id)
    outgoing = {}
    incoming = {}
    node_type = node['type']
    for vr in graph.schema.valid_relations.all():
        if vr.node_from.name == node_type:
            if not vr.relation.name in outgoing:
                outgoing[vr.relation.name] = {}
            outgoing[vr.relation.name][vr.node_to.name] = None
        if vr.node_to.name == node_type:
            if not vr.relation.name in incoming:
                incoming[vr.relation.name] = {}
            incoming[vr.relation.name][vr.node_from.name] = None
    return render_to_response('graphgamel/info.html', {'properties': properties,
                                    'relationships': relationships_list,
                                    'outgoing': simplejson.dumps(outgoing),
                                    'incoming': simplejson.dumps(incoming)})


def get_neo4j_connection(graph_id):
    graph = Graph.objects.get(pk=graph_id)
    return neo4jclient.GraphDatabase(graph.neo4jgraph.host)


def add_property(request, graph_id, node_id):
    success = False
    properties = None
    if request.method == 'GET':
        gdb = get_neo4j_connection(graph_id)
        key = request.GET['property_key']
        value = request.GET['property_value']
        if key not in RESERVED_FIELD_NAMES:
            n = gdb.node[int(node_id)]
            if key not in n.properties.keys():
                n.set(key, value)
                properties = n.properties
                success = True
        return HttpResponse(simplejson.dumps({'success': success,
                                            'properties': properties}))


def modify_property(request, graph_id, node_id):
    success = False
    properties = None
    if request.method == 'GET':
        gdb = get_neo4j_connection(graph_id)
        key = request.GET['property_key']
        value = request.GET['property_value']
        if key not in RESERVED_FIELD_NAMES:
            n = gdb.node[int(node_id)]
            if key in n.properties.keys():
                n.set(key, value)
                properties = n.properties
                success = True
        return HttpResponse(simplejson.dumps({'success': success,
                                            'properties': properties}))


def delete_property(request, graph_id, node_id):
    success = False
    properties = None
    if request.method == 'GET':
        gdb = get_neo4j_connection(graph_id)
        key = request.GET['property_key']
        if key not in RESERVED_FIELD_NAMES:
            n = gdb.node[int(node_id)]
            if key in n.properties.keys():
                n.delete(key)
                properties = n.properties
                success = True
        return HttpResponse(simplejson.dumps({'success': success,
                                            'properties': properties}))


def search_node(request, graph_id):
    if request.method == 'GET':
        gdb = get_neo4j_connection(graph_id)
        node_id = request.GET.get('node_id', None)
        result = gdb.index('id', node_id)
        if 'node_type' in request.GET:
            node_type = request.GET['node_type']
            result = [r for r in result if node_type == r.properties['type']]
        response = [{'url': r.url,
                    'neo_id': r.id,
                    'properties': r.properties} for r in result]
        return HttpResponse(simplejson.dumps({'results': response}))


def filter_by_property(nodes, prop, value):
    return [n for n in nodes if n.properties[prop] == value]
