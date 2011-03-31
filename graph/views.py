import csv
import datetime
import neo4jclient
import simplejson

from django.contrib.auth.decorators import login_required
from django.shortcuts import (render_to_response,
                                redirect,
                                HttpResponse,
                                HttpResponseRedirect)
from django.template import defaultfilters
from django.template import RequestContext

from graph.forms import UploadCSVForm
from graph.models import GraphDB, Node, Media, GraphIndex, \
                    NodeType, EdgeType
from schema.models import ValidRelation
from settings import GRAPHDB_HOST

import converters


RESERVED_FIELD_NAMES = ('_slug', '_type')
RELATIONS_PER_PAGE = 20


def index(request, error=''):
    graphs = GraphDB.objects.all()
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
    slug_id = defaultfilters.slugify(n['_slug'])[:150]
    result = filter_by_property(gdb.index('_slug', slug_id),
                                '_type', n['_type'])
    result = filter_by_property(result, '_graph', str(graph.id))
    if len(result) == 1:
        node = result[0]
        n['_slug'] = slug_id
        for key, value in n.iteritems():
            node.set(key, value)
    else:
        node = create_node(gdb, n, graph)
        created = True
    return return_function(node, created, creation_info)


def create_node(gdb, n, graph):
    original_id = n['_slug']
    n['_slug'] = defaultfilters.slugify(n['_slug'])[:150]
    node_properties = {}
    if original_id != n['_slug']:
        node_properties['id'] = original_id
    node_type_obj = NodeType.objects.filter(name=n['_type'])
    if node_type_obj:
        default_properties = node_type_obj[0].nodedefaultproperty_set.all()
        for dp in default_properties:
            node_properties[dp.key] = dp.value
    for key, value in n.items():
        node_properties[key] = value
    node = gdb.node(**node_properties)
    node.set('_url', "/".join(node.url.split('/')[-2:]))
    gdb.add_to_index('_slug', n['_slug'], node)
    gdb.add_to_index('_type', n['_type'], node)
    graph_index = GraphIndex(graph=graph,
                            node_id=n['_slug'],
                            node_type=n['_type'])
    graph.graphindex_set.add(graph_index)
    return node


def get_relationship(node1, node2, edge_type):
    for relation in node1.relationships.all():
        if relation.end == node2 and relation.type == edge_type:
            return relation
    return None


def get_node_without_connection(graph_id, node_id):
    gdb = get_graphdb_connection(GRAPHDB_HOST)
    return gdb.node[int(node_id)]


def get_relationship_without_connection(graph_id, node1, edge_type, node2):
    gdb = get_graphdb_connection(GRAPHDB_HOST)
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


def get_internal_attributes(slug, _type, graph_id, user, relation=False):
    internal_attrs = {'_slug': slug,
            '_type': _type,
            '_graph': graph_id,
            '_user': user.username,
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


def set_relationship_properties(rel_obj, edge_type, graph_id, user):
    edge_type_obj = EdgeType.objects.filter(name=edge_type)
    if edge_type_obj:
        default_properties = edge_type_obj[0].edgedefaultproperty_set.all()
        for dp in default_properties:
            rel_obj.set(dp.key, dp.value)
    slug = "%s:%s:%s" % (rel_obj.start.properties['_slug'],
                        edge_type,
                        rel_obj.end.properties['_slug'])
    inner_properties = get_internal_attributes(slug,
                                                edge_type,
                                                graph_id,
                                                user,
                                                True)
    for key, value in inner_properties.iteritems():
        rel_obj.set(key, value)
    rel_obj.set('_url', "/".join(rel_obj.url.split('/')[-2:]))


@login_required
def editor(request, graph_id):
    graph = GraphDB.objects.get(pk=graph_id)
    schema = graph.schema
    # Only show editor if user has permissions 
    # or no permissions are established
    if not validate_user(request, schema):
        return unauthorized_user(request)
    if not ValidRelation.objects.filter(schema=schema):
        error_message = 'Schema %s has no valid relations' % schema.name
        return index(request, error_message)
    if request.method == 'POST':
        gdb = neo4jclient.GraphDatabase(GRAPHDB_HOST)
        if gdb:
            data = request.POST.copy()
            if data['mode'] == 'node':
                n = get_internal_attributes(data['node_id'],
                                            data['node_type'],
                                            graph_id,
                                            request.user)
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
                node_from = get_internal_attributes(data['node_from_id'],
                                                    data['node_from_type'],
                                                    graph_id,
                                                    request.user)
                properties = simplejson.loads(data['node_from_properties'])
                node_from.update(properties)
                relation = {'_type': data['relation_type']}
                properties = simplejson.loads(data['relation_properties'])
                relation.update(properties)
                node_to = get_internal_attributes(data['node_to_id'],
                                                    data['node_to_type'],
                                                    graph_id,
                                                    request.user)
                properties = simplejson.loads(data['node_to_properties'])
                node_to.update(properties)
                edge_type = relation['_type']
                start_node = get_or_create_node(gdb, node_from, graph)
                end_node = get_or_create_node(gdb, node_to, graph)
                rel_obj, new = get_or_create_relationship(start_node,
                                                            end_node,
                                                            edge_type,
                                                            True)
                if new:
                    # Relation default and inner properties
                    set_relationship_properties(rel_obj, 
                                                data['relation_type'],
                                                graph_id,
                                                request.user)
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
        try:
            gdb = neo4jclient.GraphDatabase(GRAPHDB_HOST)
            request.session["GRAPHDB_HOST"] = GRAPHDB_HOST
        except:
            error_message = "The host %s is not available" % GRAPHDB_HOST
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


def node_info(request, graph_id, node_id, page=0):
    page = int(page)
    gdb = get_graphdb_connection(GRAPHDB_HOST)
    node = gdb.node[int(node_id)]
    # Makes sure graph_id is node_id graph
    if node['_graph'] != graph_id:
        return redirect(node_info, node['_graph'], node_id)
    properties = simplejson.dumps(node.properties)
    relationships = node.relationships.all()
    relationships_list = []
    total_pages = len(relationships)/RELATIONS_PER_PAGE
    pagination = {'page': page,
                    'start': page*RELATIONS_PER_PAGE,
                    'end': (page+1)*RELATIONS_PER_PAGE,
                    'total': total_pages,
                    'previous': max(0, page-1),
                    'next': min(total_pages, page+1)}
    for r in relationships[pagination['start']:pagination['end']]:
        relation_info = {'start_id': r.start.get('_slug', None),
                        'start_type': r.start.get('_type', None),
                        'start_neo_id': r.start.id,
                        'relation_type': r.type,
                        'relation_url': r.url,
                        'relation_id': r.url.split('/')[-1], #TODO Fix in client
                        'end_id': r.end.get('_slug', None),
                        'end_type': r.end.get('_type', None),
                        'end_neo_id': r.end.id}
        relationships_list.append(relation_info)
    graph = GraphDB.objects.get(pk=graph_id)
    node_type = node['_type']
    outgoing, incoming = graph.schema.get_incoming_and_outgoing(node_type)
    media_items = {}
    if '_media' in node.properties:
        relational_node = Node.objects.get(pk=node.properties['_media'])
        media_items['meta'] = {'id': node.properties['_media']}
        for media in relational_node.media_set.all():
            if media.media_type not in media_items:
                media_items[media.media_type] = []
            media_items[media.media_type].append({'url': media.media_file.url,
                                                'caption': media.media_caption})
    node_name = '%s(%s)' % (node.properties['_slug'],
                            node.properties['_type'])
    authorized = validate_user(request, get_schema(graph_id))
    return render_to_response('graphgamel/node_info.html',
                                    RequestContext(request, {
                                    'properties': properties,
                                    'relationships': relationships_list,
                                    'outgoing': simplejson.dumps(outgoing),
                                    'incoming': simplejson.dumps(incoming),
                                    'graph_id': graph_id,
                                    'node_id': node_id,
                                    'media_items': media_items,
                                    'node_name': node_name,
                                    'pagination': pagination,
                                    'authorized': authorized}))


def relation_info(request, graph_id, start_node_id, edge_type, end_node_id):
    gdb = get_graphdb_connection(GRAPHDB_HOST)
    start_node = gdb.node[int(start_node_id)]
    end_node = gdb.node[int(end_node_id)]
    relation = get_relationship(start_node, end_node, edge_type)
    if relation:
        properties = simplejson.dumps(relation.properties)
        start_node_properties = simplejson.dumps(relation.start.properties)
        end_node_properties = simplejson.dumps(relation.end.properties)
        authorized = validate_user(request, get_schema(graph_id))
        return render_to_response('graphgamel/relation_info.html',
                                RequestContext(request, {
                                'properties': properties,
                                'graph_id': graph_id,
                                'start_node_id': start_node_id,
                                'end_node_id': end_node_id,
                                'start_node_properties': start_node_properties,
                                'end_node_properties': end_node_properties,
                                'edge_type': edge_type,
                                'authorized': authorized}))


def get_graphdb_connection(graphdb_host):
    try:
        return neo4jclient.GraphDatabase(graphdb_host)
    except:
        return None


def get_schema(graph_id):
    return GraphDB.objects.get(pk=graph_id).schema


def validate_user(request, schema):
    allowed_users = schema.allowed_users.all()
    allowed_groups = schema.allowed_groups.all()
    user = request.user
    if allowed_users or allowed_groups:
        if user not in allowed_users and not \
            [g for g in user.groups.all() if g in allowed_groups]:
            return False
    return True


def unauthorized_user(request):
    if request.is_ajax():
        return HttpResponse(simplejson.dumps({'nopermission': True}))
    else:
        return HttpResponseRedirect('/accounts/login/?next=%s' % 
                                        request.path)


def node_property(request, graph_id, node_id, action):
    if not validate_user(request, get_schema(graph_id)):
        return unauthorized_user(request)
    key = request.GET['property_key']
    if key.startswith('_'):
        return HttpResponse(simplejson.dumps({'success': False,
                                            'internalfield': key}))
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
    if not validate_user(request, get_schema(graph_id)):
        return unauthorized_user(request)

    relation = get_relationship_without_connection(graph_id, start_node_id,
                                        edge_type, end_node_id)
    key = request.GET['property_key']
    if key.startswith('_'):
        return HttpResponse(simplejson.dumps({'success': False,
                                            'internalfield': key}))
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
                update_timestamp(element, request.user.username)
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
                update_timestamp(element, request.user.username)
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
                update_timestamp(element, request.user.username)
        return HttpResponse(simplejson.dumps({'success': success,
                                            'properties': properties}))


def search_node(request, graph_id, node_field='', _field_value=''):
    if request.method == 'GET':
        gdb = get_graphdb_connection(GRAPHDB_HOST)
        if not gdb:
            error_message = "The host %s is not available" % GRAPHDB_HOST 
            return index(request, error_message)
        field_value = request.GET.get('field_value', _field_value)
        if not node_field:
            node_field = '_slug'
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
        # Multigraph DB filtering
        result = filter_by_property(result, '_graph', graph_id)
        if node_field != '_type':
            node_type = request.GET.get('node_type', '')
        else:
            node_type = field_value
        if field_value and node_field == '_type':
            result = filter_by_property(result, '_type', node_type)
        response = [{'url': r.url,
                    'neo_id': r.id,
                    'slug': r.properties['_slug'],
                    'type': r.properties['_type']} for r in result]
        if request.is_ajax():
            return HttpResponse(simplejson.dumps({'results': response}))
        else:
            return search_results(request, graph_id, response, field_value)


def search_nodes_by_field(request, graph_id, node_field, field_value):
    return search_node(request, graph_id, node_field, field_value)


def filter_by_property(nodes, prop, value):
    return [n for n in nodes if n.properties[prop] == value]


def delete_node(request, graph_id, node_id):
    if not validate_user(request, get_schema(graph_id)):
        return unauthorized_user(request)
    success = False
    if request.is_ajax():
        gdb = get_graphdb_connection(GRAPHDB_HOST)
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


def delete_relationship(request, graph_id, node_id, relationship_id, page):
    if not validate_user(request, get_schema(graph_id)):
        return unauthorized_user(request)
    gdb = get_graphdb_connection(GRAPHDB_HOST)
    node = gdb.nodes[int(node_id)]
    for relation in node.relationships.all():
        if relationship_id == relation.url.split('/')[-1]:
            relation.delete()
            break
    return node_info(request, graph_id, node_id, page)


def add_media(request, graph_id, node_id):
    graph = GraphDB.objects.get(pk=graph_id)
    node = get_node_without_connection(graph, node_id)
    if not '_media' in node.properties:
        relational_db_node = Node(node_id=node.properties['_slug'],
                                    node_type=node.properties['_type'],
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


def add_media_link(request, graph_id, node_id):
    graph = GraphDB.objects.get(pk=graph_id)
    node = get_node_without_connection(graph, node_id)
    media_type = request.POST['media_type']
    media_link = request.POST['media_link']
    node.set(media_type, media_link)
    return redirect(node_info, graph_id, node_id)


def create_raw_relationship(request, graph_id, node_id):
    if request.method == "GET":
        gdb = get_graphdb_connection(GRAPHDB_HOST)
        start_node = gdb.nodes[int(node_id)]
        end_node = gdb.nodes[int(request.GET['destination'])]
        edge_type = request.GET['edge_type']
        if (request.GET['reversed'] == u"true"):
            start_node, end_node = end_node, start_node
        if not get_relationship(start_node, end_node, edge_type):
            relationship = getattr(start_node, edge_type)(end_node)
            # Relation default and inner properties
            set_relationship_properties(relationship,
                                        edge_type,
                                        graph_id,
                                        request.user)
    return redirect(node_info, graph_id, node_id)


def search_results(request, graph_id, results, search_string):
    if len(results) == 1:
        return redirect(node_info, graph_id, results[0]['neo_id'])
    else:
        graph = GraphDB.objects.get(pk=graph_id)
        return render_to_response('graphgamel/result_list.html',
                                    RequestContext(request, {
                                    'graph_id': graph_id,
                                    'node_types': graph.schema.get_node_types(),
                                    'result_list': results,
                                    'search_string': search_string}))


def get_autocompletion_objects(request, graph_id):
    if request.method == 'GET':
        graph = GraphDB.objects.get(pk=graph_id)
        node_type = request.GET.get('node_type', '')
        if node_type:
            results = [r.node_id
                        for r in graph.graphindex_set.filter(node_type=node_type)]
        else:
            results = ['%s (%s)' % (r.node_id, r.node_type)
                        for r in graph.graphindex_set.all()]
        return HttpResponse(simplejson.dumps(results))


def get_node_and_neighbourhood(graph_id, node_id):
    neograph = GraphDB.objects.get(pk=graph_id)
    graph = {"nodes":{}, "edges":{}}
    gdb = get_graphdb_connection(GRAPHDB_HOST)
    node = gdb.node[int(node_id)]
    properties = node.properties
    graph["nodes"][properties['_slug']] = properties
    relationships = node.relationships.all()
    edges_counter= 0
    for r in relationships:
        start_properties = r.start.properties
        properties = start_properties.copy()
        start_id = properties["_slug"]
        if start_id not in graph["nodes"]:
            graph["nodes"][start_id] = properties.copy()
        end_properties = r.end.properties
        properties = end_properties.copy()
        end_id = properties["_slug"]
        if end_id not in graph["nodes"]:
            graph["nodes"][end_id] = properties.copy()
        graph["edges"][edges_counter] = {'node1': start_id,
                                    'node2': end_id,
                                    'id': r.type}
        edges_counter += 1
    return graph


def visualize(request, graph_id, node_id):
    neograph = GraphDB.objects.get(pk=graph_id)
    graph = get_node_and_neighbourhood(graph_id, node_id)
    return render_to_response('graphgamel/graphview/explorer.html',
                                    RequestContext(request, {
                                    'json_graph': simplejson.dumps(graph),
                                    'graph_id': graph_id,
                                    'node_id': node_id}))


def get_node_from_index(request, graph_id):
    node_id = request.GET.get('node_id', None)
    node_type = request.GET.get('node_type', None)
    gdb = get_graphdb_connection(GRAPHDB_HOST)
    result = filter_by_property(gdb.index('_slug', node_id),
                                '_type', node_type)
    result = filter_by_property(result, '_graph', graph_id)
    if len(result) == 1:
        return result[0]
    else:
        return None


def expand_node(request, graph_id):
    node = get_node_from_index(request, graph_id)
    if node:
        new_graph = get_node_and_neighbourhood(graph_id, node.id)
        response_dictionary = {'success': True,
                                'new_gdata': new_graph}
    else:
        response_dictionary = {'success': False}
    return HttpResponse(simplejson.dumps(response_dictionary))


def open_node_info(request, graph_id):
    node = get_node_from_index(request, graph_id)
    return HttpResponse(simplejson.dumps({'success':True, 'node_id':node.id}))

def handle_csv_file(uploaded_file):
    csv_info = csv.reader(uploaded_file)
    return list(csv_info)


def import_manager(request):
    if request.method == 'POST':
        form = UploadCSVForm(request.POST, request.FILES)
        if form.is_valid():
            graph_id = int(request.POST['graph'])
            graph = GraphDB.objects.get(pk=graph_id)
            try:
                rows = handle_csv_file(request.FILES['csv_file'])
                row_length = len(rows[0])
            except:
                pass #TODO Print a helpful message
            node_types = graph.schema.get_node_types()
            valid_relations = []
            for vr in ValidRelation.objects.filter(schema=graph.schema):
                valid_relations.append({'node_from': vr.node_from.name,
                                        'relation': vr.relation.name,
                                        'node_to': vr.node_to.name})
            return render_to_response('graphgamel/csv/manager.html', {'rows':rows,
                        'json_data': simplejson.dumps(rows),
                        'len': range(row_length),
                        'graph_id': graph_id,
                        'node_types': node_types,
                        'relations': valid_relations,
                        'valid_relations':simplejson.dumps(valid_relations)})
    else:
        form = UploadCSVForm()
    return render_to_response('graphgamel/csv/upload.html', {'form': form})


def add_node_ajax(request, graph_id):
    if request.method == 'GET':
        graph = GraphDB.objects.get(pk=int(graph_id))
        gdb = neo4jclient.GraphDatabase(GRAPHDB_HOST)
        node = simplejson.loads(request.GET['json_node'])
        collapse = simplejson.loads(request.GET['collapse'])
        if collapse:
            new_node = get_or_create_node(gdb, node, graph)
        else:
            new_node = create_node(gdb, node, graph, collapse)
        if new_node:
            success = True
        else:
            success = False
        return HttpResponse(simplejson.dumps({'success':success}))


def add_relationship_ajax(request, graph_id):
    if request.method == 'GET':
        graph = GraphDB.objects.get(pk=int(graph_id))
        gdb = neo4jclient.GraphDatabase(GRAPHDB_HOST)
        relation_info = simplejson.loads(request.GET['json_relation'])
        node_from = {}
        node_to = {}
        node_from['id'] = relation_info['node_from']
        node_from['type'] = relation_info['node_from_type']
        node_to['id'] = relation_info['node_to']
        node_to['type'] = relation_info['node_to_type']
        relation_data = relation_info['data']
        node1 = get_or_create_node(gdb, node_from, graph)
        node2 = get_or_create_node(gdb, node_to, graph)
        rel_obj = get_or_create_relationship(node1,
                                            node2,
                                            relation_info['relation'])
        if rel_obj:
            for key, value in relation_data.iteritems():
                rel_obj.set(key, value)
            success = True

        else:
            success = False
        return HttpResponse(simplejson.dumps({'success':success}))


def export_to_gexf(request, json_graph):
    response = HttpResponse(mimetype='application/xml')
    response['Content-Disposition'] = 'attachment; filename=graph.gexf'
    gephi_format = converters.json_to_gexf(json_graph)
    response.write(gephi_format)
    return response
