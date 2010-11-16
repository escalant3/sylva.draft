import neo4jclient
import simplejson

from django.contrib.auth.decorators import login_required
from django.shortcuts import (render_to_response,
                                redirect,
                                HttpResponse,
                                HttpResponseRedirect)
from django.template import defaultfilters
from django.template import RequestContext

from graph.models import Neo4jGraph, Node, Media, GraphIndex, \
                    NodeType, EdgeType


RESERVED_FIELD_NAMES = ('id', 'type')


def index(request, error=''):
    graphs = Neo4jGraph.objects.all()
    messages = request.session.get('messages', None)
    if not messages:
        request.session['messages'] = []
        messages = []
    return render_to_response('graphgamel/index.html',
                        RequestContext(request, {
                        'graph_list': graphs,
                        'error_message': error}))


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
    if 'messages' not in request.session:
        request.session['messages'] = []
    request.session['messages'].insert(0, {'title': title,
                                            'element_id': element_id,
                                            'element_type': element_type,
                                            'action_type': action_type,
                                            'text': text})
    request.session['messages'] = request.session['messages'][:10]


def get_or_create_node(gdb, n, graph, creation_info=False):
    created = False
    n['id'] = defaultfilters.slugify(n['id'])[:150]
    result = filter_by_property(gdb.index('id', n['id']),
                                'type', n['type'])
    if len(result) == 1:
        node = result[0]
        for key, value in n.iteritems():
            node.set(key, value)
    else:
        node_properties = {}
        node_type_obj = NodeType.objects.filter(name=n['type'])
        if node_type_obj:
            default_properties = node_type_obj[0].nodedefaultproperty_set.all()
            for dp in default_properties:
                node_properties[dp.key] = dp.value
        for key, value in n.items():
            node_properties[key] = value
        node = gdb.node(**node_properties)
        gdb.add_to_index('id', n['id'], node)
        gdb.add_to_index('type', n['type'], node)
        created = True
        graph_index = GraphIndex(graph=graph,
                                node_id=n['id'],
                                node_type=n['type'])
        graph.graphindex_set.add(graph_index)
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


@login_required
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
                if new:
                    edge_type_obj = EdgeType.objects.filter(
                                        name=data['relation_type'])
                    if edge_type_obj:
                        default_properties = edge_type_obj[0].edgedefaultproperty_set.all()
                        for dp in default_properties:
                            rel_obj.set(dp.key, dp.value)
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
            error_message = "The host %s is not available" % host
            return index(request, error_message)
        form_structure = simplejson.dumps(schema.get_dictionaries())
        node_types = simplejson.dumps(schema.get_node_types())
        request.session['form_structure'] = form_structure
        request.session['node_types'] = node_types
    form_structure = request.session['form_structure']
    node_types = request.session['node_types']
    messages = request.session.get('messages', [])
    json_graph = schema.get_json_schema_graph()
    return render_to_response('graphgamel/editor.html',
                        RequestContext(request, {
                        'schema': schema,
                        'history_list': messages,
                        'form_structure': form_structure,
                        'node_types': node_types,
                        'json_graph': json_graph,
                        'graph_id': graph_id}))


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
    media_items = {}
    if '_media' in node.properties:
        relational_node = Node.objects.get(pk=node.properties['_media'])
        media_items['meta'] = {'id': node.properties['_media']}
        for media in relational_node.media_set.all():
            if media.media_type not in media_items:
                media_items[media.media_type] = []
            media_items[media.media_type].append({'url': media.media_file.url,
                                                'caption': media.media_caption})
    node_name = '%s(%s)' % (node.properties['id'],
                            node.properties['type'])
    return render_to_response('graphgamel/node_info.html',
                                    RequestContext(request, {
                                    'properties': properties,
                                    'relationships': relationships_list,
                                    'outgoing': simplejson.dumps(outgoing),
                                    'incoming': simplejson.dumps(incoming),
                                    'graph_id': graph_id,
                                    'node_id': node_id,
                                    'media_items': media_items,
                                    'node_name': node_name}))


def relation_info(request, graph_id, start_node_id, edge_type, end_node_id):
    gdb = get_neo4j_connection(graph_id)
    start_node = gdb.node[int(start_node_id)]
    end_node = gdb.node[int(end_node_id)]
    relation = get_relationship(start_node, end_node, edge_type)
    if relation:
        properties = simplejson.dumps(relation.properties)
        start_node_properties = simplejson.dumps(relation.start.properties)
        end_node_properties = simplejson.dumps(relation.end.properties)
        return render_to_response('graphgamel/relation_info.html',
                                RequestContext(request, {
                                'properties': properties,
                                'graph_id': graph_id,
                                'start_node_id': start_node_id,
                                'end_node_id': end_node_id,
                                'start_node_properties': start_node_properties,
                                'end_node_properties': end_node_properties,
                                'edge_type': edge_type}))


def get_neo4j_connection(graph_id):
    graph = Neo4jGraph.objects.get(pk=graph_id)
    try:
        return neo4jclient.GraphDatabase(graph.host)
    except:
        return None


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


def search_node(request, graph_id, node_field='', _field_value=''):
    if request.method == 'GET':
        gdb = get_neo4j_connection(graph_id)
        if not gdb:
            graph = Neo4jGraph.objects.get(pk=graph_id)
            host = graph.host
            error_message = "The host %s is not available" % host
            return index(request, error_message)
        field_value = request.GET.get('field_value', _field_value)
        if not node_field:
            node_field = 'id'
        try:
            if field_value:
                result = gdb.index(node_field, field_value)
                # Strings including node_type
                if not result and field_value.endswith(')'):
                    clean_value = field_value[0:field_value.rfind('(')-1]
                    result = gdb.index(node_field, clean_value)
            else:
                result = []
        except neo4jclient.NotFoundError:
            result = []
        if node_field != 'type':
            node_type = request.GET.get('node_type', '')
        else:
            node_type = field_value
        if field_value and node_field == 'type':
            result = [r for r in result if node_type == r.properties['type']]
        response = [{'url': r.url,
                    'neo_id': r.id,
                    'properties': r.properties} for r in result]
        if request.is_ajax():
            return HttpResponse(simplejson.dumps({'results': response}))
        else:
            return search_results(request, graph_id, response, field_value)


def search_nodes_by_field(request, graph_id, node_field, field_value):
    return search_node(request, graph_id, node_field, field_value)


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
        media_caption = request.POST['media_caption']
        media_file = request.FILES['media_file']
        media = Media(node=relational_db_node,
                    media_type=media_type,
                    media_caption=media_caption,
                    media_file=media_file)
        media.save()
    return redirect(node_info, graph_id, node_id)


def create_raw_relationship(request, graph_id, node_id):
    if request.method == "GET":
        gdb = get_neo4j_connection(graph_id)
        start_node = gdb.nodes[int(node_id)]
        end_node = gdb.nodes[int(request.GET['destination'])]
        edge_type = request.GET['edge_type']
        if (request.GET['reversed']):
            start_node, end_node = end_node, start_node
        if not get_relationship(start_node, end_node, edge_type):
            getattr(start_node, edge_type)(end_node)
    return redirect(node_info, graph_id, node_id)


def search_results(request, graph_id, results, search_string):
    if len(results) == 1:
        return redirect(node_info, graph_id, results[0]['neo_id'])
    else:
        graph = Neo4jGraph.objects.get(pk=graph_id)
        return render_to_response('graphgamel/result_list.html',
                                    RequestContext(request, {
                                    'graph_id': graph_id,
                                    'node_types': graph.schema.get_node_types(),
                                    'result_list': results,
                                    'search_string': search_string}))


def get_autocompletion_objects(request, graph_id):
    if request.method == 'GET':
        graph = Neo4jGraph.objects.get(pk=graph_id)
        node_type = request.GET.get('node_type', '')
        if node_type:
            results = [r.node_id
                        for r in graph.graphindex_set.filter(node_type=node_type)]
        else:
            results = ['%s (%s)' % (r.node_id, r.node_type)
                        for r in graph.graphindex_set.all()]
        return HttpResponse(simplejson.dumps(results))


def get_node_and_neighbourhood(graph_id, node_id, visual_data):
    neograph = Neo4jGraph.objects.get(pk=graph_id)
    graph = {"nodes":{}, "edges":{}}
    gdb = get_neo4j_connection(graph_id)
    node = gdb.node[int(node_id)]
    properties = node.properties
    graph["nodes"][properties['id']] = visual_data[properties['type']]
    graph["nodes"][properties['id']].update(properties)
    relationships = node.relationships.all()
    edges_counter= 0
    for r in relationships:
        start_properties = r.start.properties
        properties = start_properties.copy()
        start_id = properties["id"]
        if start_id not in graph["nodes"]:
            graph["nodes"][start_id] = visual_data[properties['type']].copy()
            graph["nodes"][start_id].update(properties.copy())
        end_properties = r.end.properties
        properties = end_properties.copy()
        end_id = properties["id"]
        if end_id not in graph["nodes"]:
            graph["nodes"][end_id] = visual_data[properties['type']].copy()
            graph["nodes"][end_id].update(properties.copy())
        graph["edges"][edges_counter] = {'node1': start_id,
                                    'node2': end_id,
                                    'id': r.type}
        edges_counter += 1
    return graph


def visualize(request, graph_id, node_id):
    neograph = Neo4jGraph.objects.get(pk=graph_id)
    visual_data = neograph.schema.get_node_visual_data()
    request.session['visual_data'] = visual_data
    graph = get_node_and_neighbourhood(graph_id, node_id, visual_data)
    style_list = [(key, value) for key, value
                        in visual_data.iteritems()]
    return render_to_response('graphgamel/graphview/explorer.html',
                                    RequestContext(request, {
                                    'json_graph': simplejson.dumps(graph),
                                    'node_style_list':style_list,
                                    'graph_id': graph_id,
                                    'node_id': node_id}))


def expand_node(request, graph_id):
    node_id = request.GET.get('node_id', None)
    node_type = request.GET.get('node_type', None)
    gdb = get_neo4j_connection(graph_id)
    result = filter_by_property(gdb.index('id', node_id),
                                'type', node_type)
    if len(result) == 1:
        node = result[0]
    visual_data = request.session.get('visual_data', None)
    new_graph = get_node_and_neighbourhood(graph_id, node.id, visual_data)
    response_dictionary = {'success': True,
                            'new_gdata': new_graph}
    return HttpResponse(simplejson.dumps(response_dictionary))
