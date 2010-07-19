import neo4jclient
import simplejson

from django.shortcuts import render_to_response, redirect, HttpResponse

from graph.models import Neo4jGraph, Node, Media


RESERVED_FIELD_NAMES = ('id', 'type')


def index(request):
    graphs = Neo4jGraph.objects.all()
    messages = request.session.get('messages', None)
    if not messages:
        request.session['messages'] = []
        messages = []
    return render_to_response('graphgamel/index.html', {
                        'graph_list': graphs})


def return_function(obj, value, show_info):
    if show_info:
        return obj, value
    else:
        return obj


def add_message(request, text,
                title='',
                element_id='',
                element_type='',
                action_type=''):
    request.session['messages'].insert(0, {'title': title,
                                            'element_id': element_id,
                                            'element_type': element_type,
                                            'action_type': action_type,
                                            'text': text})
    request.session['messages'] = request.session['messages'][:10]


def get_or_create_node(gdb, n, graph, creation_info=False):
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


def get_relationship(node1, node2, edge_type):
    for relation in node1.relationships.all():
        if relation.end == node2 and relation.type == edge_type:
            return relation
    return None


def get_node_without_connection(graph_id, node_id):
    gdb = get_neo4j_connection(graph_id)
    return gdb.node[int(node_id)]


def get_relationship_without_connection(graph_id, node1, edge_type, node2):
    gdb = get_neo4j_connection(graph_id)
    start_node = gdb.nodes[int(node1)]
    end_node = gdb.nodes[int(node2)]
    return get_relationship(start_node, end_node, edge_type)


def get_or_create_relationship(node1, node2, edge_type, creation_info=False):
    created = True
    relation = get_relationship(node1, node2, edge_type)
    if relation:
        created = False
    else:
        relation = getattr(node1, edge_type)(node2)
    return return_function(relation, created, creation_info)


def editor(request, graph_id):
    graph = Neo4jGraph.objects.get(pk=graph_id)
    schema = graph.schema
    if request.method == 'POST':
        gdb = neo4jclient.GraphDatabase(graph.host)
        if gdb:
            data = request.POST.copy()
            if data['mode'] == 'node':
                n = {'id': data['node_id'], 'type': data['node_type']}
                properties = simplejson.loads(data['node_properties'])
                n.update(properties)
                node, new = get_or_create_node(gdb, n, graph, True)
                if new:
                    add_message(request,
                                title='Created %s' % data['node_id'],
                                action_type='add',
                                element_id=node.id,
                                element_type='node',
                                text='%s node' % data['node_type'])
                else:
                    add_message(request,
                                title='Modified %s' % data['node_id'],
                                action_type='add',
                                element_id=node.id,
                                element_type='node',
                                text='%s node' % data['node_type'])
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
                node1 = get_or_create_node(gdb, node_from, graph)
                node2 = get_or_create_node(gdb, node_to, graph)
                rel_obj, new = get_or_create_relationship(node1,
                                                            node2,
                                                            edge_type,
                                                            True)
                for key, value in relation.iteritems():
                    rel_obj.set(key, value)
                if new:
                    add_message(request,
                                title='Created %s' % edge_type,
                                action_type='add',
                                element_type='edge',
                                element_id=(rel_obj.start.id,
                                            rel_obj.type,
                                            rel_obj.end.id),
                                text='%s(%s) %s %s(%s) relation' %
                                        (data['node_from_id'],
                                        data['node_from_type'],
                                        edge_type,
                                        data['node_to_id'],
                                        data['node_to_type']))
                else:
                    add_message(request,
                                title='Modified %s' % edge_type,
                                action_type='change',
                                element_type='edge',
                                element_id=(rel_obj.start.id,
                                            rel_obj.type,
                                            rel_obj.end.id),
                                text='%s(%s) %s %s(%s) relation' %
                                        (data['node_from_id'],
                                        data['node_from_type'],
                                        edge_type,
                                        data['node_to_id'],
                                        data['node_to_type']))
    else:
        # Check connection
        host = graph.host
        try:
            gdb = neo4jclient.GraphDatabase(host)
            request.session["host"] = host
        except:
            return redirect(index)
        form_structure = simplejson.dumps(schema.get_dictionaries())
        node_types = simplejson.dumps(schema.get_node_types())
        request.session['form_structure'] = form_structure
        request.session['node_types'] = node_types
    form_structure = request.session['form_structure']
    node_types = request.session['node_types']
    messages = request.session['messages']
    return render_to_response('graphgamel/editor.html', {
                        'schema': schema,
                        'history_list': messages,
                        'form_structure': form_structure,
                        'node_types': node_types,
                        'graph_id': graph_id})


def node_info(request, graph_id, node_id):
    gdb = get_neo4j_connection(graph_id)
    node = gdb.node[int(node_id)]
    properties = simplejson.dumps(node.properties)
    relationships = node.relationships.all()
    relationships_list = []
    for r in relationships:
        relation_info = {'start_id': r.start.get('id', None),
                        'start_type': r.start.get('type', None),
                        'start_neo_id': r.start.id,
                        'relation_type': r.type,
                        'relation_url': r.url,
                        'end_id': r.end.get('id', None),
                        'end_type': r.end.get('type', None),
                        'end_neo_id': r.end.id}
        relationships_list.append(relation_info)
    graph = Neo4jGraph.objects.get(pk=graph_id)
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
    media = []
    if '_media' in node.properties:
        relational_node = Node.objects.get(pk=node.properties['_media'])
        media = [{'type':media.media_type, 
                    'url': media.media_file.url}
                    for media in relational_node.media_set.all()]
    node_name = '%s(%s)' % (node.properties['id'],
                            node.properties['type'])
    return render_to_response('graphgamel/node_info.html', {'properties': properties,
                                    'relationships': relationships_list,
                                    'outgoing': simplejson.dumps(outgoing),
                                    'incoming': simplejson.dumps(incoming),
                                    'graph_id': graph_id,
                                    'node_id': node_id,
                                    'media_items': media,
                                    'node_name': node_name})


def relation_info(request, graph_id, start_node_id, edge_type, end_node_id):
    gdb = get_neo4j_connection(graph_id)
    start_node = gdb.node[int(start_node_id)]
    end_node = gdb.node[int(end_node_id)]
    relation = get_relationship(start_node, end_node, edge_type)
    if relation:
        properties = simplejson.dumps(relation.properties)
        return render_to_response('graphgamel/relation_info.html', {
                                'properties': properties,
                                'graph_id': graph_id,
                                'start_node_id': start_node_id,
                                'end_node_id': end_node_id,
                                'edge_type': edge_type})


def get_neo4j_connection(graph_id):
    graph = Neo4jGraph.objects.get(pk=graph_id)
    return neo4jclient.GraphDatabase(graph.neo4jgraph.host)


def node_property(request, graph_id, node_id, action):
    node = get_node_without_connection(graph_id, node_id)
    if node:
        if action == 'add':
            return add_property(request, node)
        elif action == 'modify':
            return modify_property(request, node)
        elif action == 'delete':
            return delete_property(request, node)


def relation_property(request, graph_id, start_node_id,
                            edge_type, end_node_id, action):
    relation = get_relationship_without_connection(graph_id, start_node_id,
                                        edge_type, end_node_id)
    if relation:
        if action == 'add':
            return add_property(request, relation)
        elif action == 'modify':
            return modify_property(request, relation)
        elif action == 'delete':
            return delete_property(request, relation)


def add_property(request, element):
    success = False
    properties = None
    if request.method == 'GET':
        key = request.GET['property_key']
        value = request.GET['property_value']
        if key not in RESERVED_FIELD_NAMES and not key.startswith('_'):
            if key not in element.properties.keys():
                element.set(key, value)
                properties = element.properties
                success = True
        return HttpResponse(simplejson.dumps({'success': success,
                                            'properties': properties}))


def modify_property(request, element):
    success = False
    properties = None
    if request.method == 'GET':
        key = request.GET['property_key']
        value = request.GET['property_value']
        if key not in RESERVED_FIELD_NAMES and not key.startswith('_'):
            if key in element.properties.keys():
                element.set(key, value)
                properties = element.properties
                success = True
        return HttpResponse(simplejson.dumps({'success': success,
                                            'properties': properties}))


def delete_property(request, element):
    success = False
    properties = None
    if request.method == 'GET':
        key = request.GET['property_key']
        if key not in RESERVED_FIELD_NAMES and not key.startswith('_'):
            if key in element.properties.keys():
                element.delete(key)
                properties = element.properties
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


def delete_node(request, graph_id, node_id):
    success = False
    if request.is_ajax():
        gdb = get_neo4j_connection(graph_id)
        try:
            # TODO API corrupts database
            if False:
                gdb.nodes[int(node_id)].delete()
                success = True
            messages = ["Node deleted"]
        except:
            pass
    return HttpResponse(simplejson.dumps({'success': success,
                                        'messages': messages}))


def add_media(request, graph_id, node_id):
    success = False
    graph = Neo4jGraph.objects.get(pk=graph_id)
    node = get_node_without_connection(graph, node_id)
    if not '_media' in node.properties:
        relational_db_node = Node(node_id=node.properties['id'],
                                    node_type=node.properties['type'],
                                    graph=graph)
        relational_db_node.save()
        node.set('_media', relational_db_node.id)
    else:
        relational_db_node = Node.objects.get(pk=node.properties['_media'])
    if request.method == "POST":
        media_type = request.POST['media_type']
        media_file = request.FILES['media_file']
        media = Media(node=relational_db_node,
                    media_type=media_type,
                    media_file=media_file)
        media.save()
        success = True
    return node_info(request, graph_id, node_id)
