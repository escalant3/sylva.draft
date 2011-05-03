import csv
import neo4jrestclient as neo4jclient

import simplejson

from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.shortcuts import (render_to_response,
                                redirect,
                                HttpResponse,
                                HttpResponseRedirect)
from django.template import defaultfilters
from django.template import RequestContext

from graph.forms import UploadCSVForm, get_form_for_nodetype
from graph.models import Node, Media
from graph.utils import (create_node, search_in_index, filter_by_property,
                         get_internal_attributes, update_timestamp)
from schema.models import ValidRelation, NodeType, EdgeType, GraphDB
from settings import GRAPHDB_HOST

import converters


RESERVED_FIELD_NAMES = ('_slug', '_type')
RELATIONS_PER_PAGE = 20


def index(request, error=''):
    user = request.user
    graphs = [{'graph': g,
        'can_edit_schema': user.has_perm('schema.%s_can_edit_schema' % g.name),
        'can_edit': user.has_perm('schema.%s_can_edit' % g.name),
        'can_delete': user.has_perm('schema.%s_can_delete' % g.name),
        'can_edit_properties': \
            user.has_perm('schema.%s_can_edit_properties' % g.name),
        'can_edit_permissions': \
            user.has_perm('schema.%s_can_edit_permissions' % g.name)}
            for g in GraphDB.objects.all()
            if g.public or user.has_perm("schema.%s_can_see" % g.name)]
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
    result = search_in_index(gdb, slug_id, n['_type'], str(graph.id))
    if len(result) == 1:
        node = result[0]
        n['_slug'] = slug_id
        for key, value in n.iteritems():
            node.set(key, value)
    else:
        node = create_node(gdb, n, graph)
        created = True
    return return_function(node, created, creation_info)


def get_relationship(gdb, node1, node2, edge_type):
    idx = gdb.relationships.indexes.get('sylva_relationships')
    slug = "%s:%s:%s" % (node1['_slug'],
                        edge_type,
                        node2['_slug'])
    result = idx.get('_slug')[slug]
    return result[0] if result else None


def get_node_without_connection(graph_id, node_id):
    gdb = get_graphdb_connection(GRAPHDB_HOST)
    return gdb.node[int(node_id)]


def get_relationship_without_connection(graph_id, node1, edge_type, node2):
    gdb = get_graphdb_connection(GRAPHDB_HOST)
    start_node = gdb.nodes[int(node1)]
    end_node = gdb.nodes[int(node2)]
    return get_relationship(gdb, start_node, end_node, edge_type)


def get_or_create_relationship(gdb, node1, node2, edge_type,
                                creation_info=False):
    created = True
    relation = get_relationship(gdb, node1, node2, edge_type)
    if relation:
        created = False
    else:
        relation = getattr(node1, edge_type)(node2)
    return return_function(relation, created, creation_info)


def set_relationship_properties(gdb, rel_obj, edge_type, graph_id, user):
    edge_type_obj = EdgeType.objects.filter(name=edge_type)
    if edge_type_obj:
        default_properties = edge_type_obj[0].edgeproperty_set.all()
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
    idx = gdb.relationships.indexes.get('sylva_relationships')
    idx['_slug'][slug] = rel_obj
    idx['_type'][edge_type] = rel_obj
    idx['_graph'][graph_id] = rel_obj


@login_required
def editor(request, graph_id):
    graph = GraphDB.objects.get(pk=graph_id)
    if not request.user.has_perm("schema.%s_can_edit" % graph.name):
        return unauthorized_user(request)
    if not ValidRelation.objects.filter(graph=graph):
        error_message = 'Graph %s has no valid relations' % graph.name
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
                # Check if it is a valid relationship
                if not graph.is_valid_relationship(data['node_from_type'],
                                                data['relation_type'],
                                                data['node_to_type']):
                    raise Exception('Relationship invalid for %s graph' % \
                                    graph.name)
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
                rel_obj, new = get_or_create_relationship(gdb,
                                                            start_node,
                                                            end_node,
                                                            edge_type,
                                                            True)
                if new:
                    # Relation default and inner properties
                    set_relationship_properties(gdb,
                                                rel_obj,
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
                                element_id=rel_obj.id,
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
                                element_id=rel_obj.id,
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
    node_types = simplejson.dumps([n.name for n in graph.nodetype_set.all()])
    form_structure = simplejson.dumps(graph.get_dictionaries())
    messages = request.session.get('messages', [])
    json_graph = graph.get_json_schema_graph()
    return render_to_response('graphgamel/editor.html',
                        RequestContext(request, {
                        'graph': graph,
                        'history_list': messages,
                        'form_structure': form_structure,
                        'node_types': node_types,
                        'json_graph': json_graph,
                        'graph_id': graph_id}))


def node_info(request, graph_id, node_id, page=0):
    graph = GraphDB.objects.get(pk=graph_id)
    if not graph.public and \
            not request.user.has_perm("schema.%s_can_see" % graph.name):
        return unauthorized_user(request)
    page = int(page)
    gdb = get_graphdb_connection(GRAPHDB_HOST)
    node = gdb.node[int(node_id)]
    # Makes sure graph_id is node_id graph
    if node['_graph'] != graph_id:
        return redirect(node_info, node['_graph'], node_id)
    properties = simplejson.dumps(node.properties)
    relationships = node.relationships.all()
    relationships_list = []
    total_pages = len(relationships) / RELATIONS_PER_PAGE
    pagination = {'page': page,
                    'start': page * RELATIONS_PER_PAGE,
                    'end': (page + 1) * RELATIONS_PER_PAGE,
                    'total': total_pages,
                    'previous': max(0, page - 1),
                    'next': min(total_pages, page + 1)}
    for r in relationships[pagination['start']:pagination['end']]:
        relation_info = {'start_id': r.start.get('_slug', None),
                        'start_type': r.start.get('_type', None),
                        'start_neo_id': r.start.id,
                        'relation_type': r.type,
                        'relation_url': r.url,
                        'relation_id': r.id,
                        'end_id': r.end.get('_slug', None),
                        'end_type': r.end.get('_type', None),
                        'end_neo_id': r.end.id}
        relationships_list.append(relation_info)
    node_type = node['_type']
    outgoing, incoming = graph.get_incoming_and_outgoing(node_type)
    media_items = {}
    if '_media' in node.properties:
        relational_node = Node.objects.get(pk=node.properties['_media'])
        media_items['meta'] = {'id': node.properties['_media']}
        for media in relational_node.media_set.all():
            if media.media_type not in media_items:
                media_items[media.media_type] = []
            media_items[media.media_type].append({
                                        'url': media.media_file.url,
                                        'caption': media.media_caption})
    node_name = '%s(%s)' % (node.properties['_slug'],
                            node.properties['_type'])
    permissions = get_permissions(request.user, graph.name)
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
                                    'permission': permissions}))


def relation_info(request, graph_id, relationship_id):
    graph = GraphDB.objects.get(pk=graph_id)
    if not graph.public and \
            not request.user.has_perm("schema.%s_can_see" % graph.name):
        return unauthorized_user(request)
    gdb = get_graphdb_connection(GRAPHDB_HOST)
    relation = gdb.relationships[int(relationship_id)]
    properties = simplejson.dumps(relation.properties)
    start_node = "%s (%s)" % (relation.start['_slug'],
                            relation.start['_type'])
    end_node = "%s (%s)" % (relation.end['_slug'],
                             relation.end['_type'])
    permissions = get_permissions(request.user, graph.name)
    relation_id = relation.url.split('/')[-1]
    return render_to_response('graphgamel/relation_info.html',
                            RequestContext(request, {
                            'properties': properties,
                            'graph_id': graph_id,
                            'relation_id': relation_id,
                            'start_node_id': relation.start.id,
                            'end_node_id': relation.end.id,
                            'start_node': start_node,
                            'end_node': end_node,
                            'edge_type': relation.type,
                            'permission': permissions}))


def get_permissions(user, graph):
    return {'can_add': user.has_perm('schema.%s_can_add_data' % graph),
            'can_edit': user.has_perm('schema.%s_can_edit_data' % graph),
            'can_delete': user.has_perm('schema.%s_can_delete_data' % graph)}


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
    key = request.GET['property_key']
    if key.startswith('_'):
        return HttpResponse(simplejson.dumps({'success': False,
                                            'internalfield': key}))
    node = get_node_without_connection(graph_id, node_id)
    graph = GraphDB.objects.get(pk=graph_id)
    if node:
        if action == 'add':
            if not request.user.has_perm('schema.%s_can_add_data'
                                            % graph.name):
                return unauthorized_user(request)
            return add_property(request, node)
        elif action == 'modify':
            if not request.user.has_perm('schema.%s_can_edit_data'
                                            % graph.name):
                return unauthorized_user(request)
            return modify_property(request, node)
        elif action == 'delete':
            if not request.user.has_perm('schema.%s_can_delete_data'
                                            % graph.name):
                return unauthorized_user(request)
            node_type = NodeType.objects.get(name=node['_type'],
                                            graph=graph)
            np = node_type.nodeproperty_set.filter(key=key)
            if np and np[0].required:
                    return HttpResponse(simplejson.dumps({'success': False,
                                                        'required': key}))
            return delete_property(request, node)


def relation_property(request, graph_id, relationship_id, action):
    key = request.GET['property_key']
    if key.startswith('_'):
        return HttpResponse(simplejson.dumps({'success': False,
                                            'internalfield': key}))
    gdb = get_graphdb_connection(GRAPHDB_HOST)
    relation = gdb.relationships[int(relationship_id)]
    graph = GraphDB.objects.get(pk=graph_id)
    if relation:
        if action == 'add':
            if not request.user.has_perm('schema.%s_can_add_data'
                                            % graph.name):
                return unauthorized_user(request)
            return add_property(request, relation)
        elif action == 'modify':
            if not request.user.has_perm('schema.%s_can_edit_data'
                                            % graph.name):
                return unauthorized_user(request)
            return modify_property(request, relation)
        elif action == 'delete':
            if not request.user.has_perm('schema.%s_can_delete_data'
                                            % graph.name):
                return unauthorized_user(request)
            edge_type = EdgeType.objects.get(name=relation['_type'],
                                            graph=graph)
            ep = edge_type.edgeproperty_set.filter(key=key)
            if ep and ep[0].required:
                    return HttpResponse(simplejson.dumps({'success': False,
                                                        'required': key}))
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
    graph = GraphDB.objects.get(pk=graph_id)
    predef_properties = []
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
                idx = gdb.nodes.indexes.get('sylva_nodes')
                result = idx.get(node_field)[field_value]
                # Strings including node_type
                if not result and field_value.endswith(')'):
                    clean_value = field_value[0:field_value.rfind('(') - 1]
                    result = idx.get(node_field)[clean_value]
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
            node_type_obj= NodeType.objects.filter(name=field_value,
                                                graph=graph)[0]
            predef_properties = ['_type']
            predef_properties.extend([n.key \
                            for n in node_type_obj.nodeproperty_set.all()])
        response = [{'url': reverse('graph.views.node_info',
                                    args=[graph_id, r.id]),
                    'neo_id': r.id,
                    'properties': {'slug': r.properties['_slug'],
                                'type': r.properties['_type']},
                    'values': get_element_predefs(predef_properties, r)}
                    for r in result]
        if request.is_ajax():
            return HttpResponse(simplejson.dumps({'results': response}))
        else:
            return search_results(request, graph_id, response,
                                    predef_properties, field_value)


def get_element_predefs(props, element):
    properties = []
    for p in props:
        properties.append(element.get(p, ''))
    return properties


def search_nodes_by_field(request, graph_id, node_field, field_value):
    return search_node(request, graph_id, node_field, field_value)


def search_relationships_by_field(request, graph_id, field, value):
    graph = GraphDB.objects.get(pk=graph_id)
    if not graph.public and \
            not request.user.has_perm("schema.%s_can_see" % graph.name):
        return unauthorized_user(request)
    gdb = get_graphdb_connection(GRAPHDB_HOST)
    idx = gdb.relationships.indexes.get('sylva_relationships')
    result = idx.get(field)[value]
    result = filter_by_property(result, '_graph', graph_id)
    if field == '_type':
        edge_type_obj= EdgeType.objects.filter(name=value,
                                                graph=graph)[0]
        predef_properties = ['_type']
        predef_properties.extend([e.key \
                            for e in edge_type_obj.edgeproperty_set.all()])
    else:
        predef_properties = []

    response = [{'url': reverse('graph.views.relation_info',
                                args=[graph_id, r.id]),
                'neo_id': r.id,
                'values': get_element_predefs(predef_properties,r),
                'properties': {'slug': r.properties['_slug'],
                                'type': r.properties['_type']}}
                    for r in result]
    return search_results(request, graph_id, response,
                            predef_properties, value)


def delete_node(request, graph_id, node_id):
    graph = GraphDB.objects.get(pk=graph_id)
    if not request.user.has_perm('schema.%s_can_delete_data' % graph.name):
        return unauthorized_user(request)
    gdb = get_graphdb_connection(GRAPHDB_HOST)
    node = gdb.nodes[int(node_id)]
    delete_sylva_node(graph, node)
    return redirect(search_node, graph_id)


def delete_sylva_node(graph, node):
    for relation in node.relationships.all():
        relation.delete()
    media_nodes = Node.objects.filter(graph=graph)
    for media_node in media_nodes:
        media_node.media_set.all().delete()
        media_node.delete()
    node.delete()


def delete_relationship(request, graph_id, node_id, relationship_id, page):
    graph = GraphDB.objects.get(pk=graph_id)
    if not request.user.has_perm('schema.%s_can_delete_data' % graph.name):
        return unauthorized_user(request)
    gdb = get_graphdb_connection(GRAPHDB_HOST)
    relation = gdb.relationships[int(relationship_id)]
    relation.delete()
    return node_info(request, graph_id, node_id, page)


def add_media(request, graph_id, node_id):
    graph = GraphDB.objects.get(pk=graph_id)
    if not request.user.has_perm("schema.%s_can_add_data" % graph.name):
        return unauthorized_user(request)
    node = get_node_without_connection(graph, node_id)
    if not '_media' in node.properties:
        sql_node = Node.objects.filter(
                    graph=graph,
                    node_id=node['_slug'],
                    node_type=node['_type'])[0]
        node.set('_media', sql_node.id)
    else:
        sql_node = Node.objects.get(pk=node.properties['_media'])
    if request.method == "POST":
        media_type = request.POST['media_type']
        media_caption = request.POST['media_caption']
        media_file = request.FILES['media_file']
        media = Media(node=sql_node,
                    media_type=media_type,
                    media_caption=media_caption,
                    media_file=media_file)
        media.save()
    return redirect(node_info, graph_id, node_id)


def add_media_link(request, graph_id, node_id):
    graph = GraphDB.objects.get(pk=graph_id)
    if not request.user.has_perm("schema.%s_can_add_data" % graph.name):
        return unauthorized_user(request)
    node = get_node_without_connection(graph, node_id)
    media_type = request.POST['media_type']
    media_link = request.POST['media_link']
    node.set(media_type, media_link)
    return redirect(node_info, graph_id, node_id)


def create_raw_relationship(request, graph_id, node_id):
    graph = GraphDB.objects.get(pk=graph_id)
    if not request.user.has_perm('schema.%s_can_add_data' % graph.name):
        return unauthorized_user(request)
    if request.method == "GET":
        gdb = get_graphdb_connection(GRAPHDB_HOST)
        start_node = gdb.nodes[int(node_id)]
        end_node = gdb.nodes[int(request.GET['destination'])]
        edge_type = request.GET['edge_type']
        if (request.GET['reversed'] == u"true"):
            start_node, end_node = end_node, start_node
        if not graph.is_valid_relationship(start_node['_type'],
                                        edge_type,
                                        end_node['_type']):
            raise Exception('Relationship invalid for %s graph' % \
                                    graph.name)
        if not get_relationship(gdb, start_node, end_node, edge_type):
            relationship = getattr(start_node, edge_type)(end_node)
            # Relation default and inner properties
            set_relationship_properties(gdb,
                                        relationship,
                                        edge_type,
                                        graph_id,
                                        request.user)
    return redirect(node_info, graph_id, node_id)


def search_results(request, graph_id, node_results, 
                predefs, search_string):
    graph = GraphDB.objects.get(pk=graph_id)
    node_types = [n.name for n in graph.nodetype_set.all()]
    edge_types = [e.name for e in graph.edgetype_set.all()]
    search_nodetypes = graph.nodetype_set.filter(name__iexact=search_string)
    if search_nodetypes:
        search_nodetype = search_nodetypes[0]
    else:
        search_nodetype = None
    return render_to_response('graphgamel/result_list.html',
                                RequestContext(request, {
                                'graph_id': graph_id,
                                'node_types': node_types,
                                'edge_types': edge_types,
                                'result_list':
                                    node_results,
                                'predefs':
                                    predefs,
                                'search_string': search_string,
                                'search_nodetype': search_nodetype}))


def get_autocompletion_objects(request, graph_id):
    graph = GraphDB.objects.get(pk=graph_id)
    if not graph.public and \
            not request.user.has_perm('schema.%s_can_see' % graph.name):
        return unauthorized_user(request)
    if request.method == 'GET':
        node_type = request.GET.get('node_type', '')
        if node_type:
            results = [r.node_id
                        for r in graph.node_set.filter(
                                        node_type=node_type)]
        else:
            results = ['%s (%s)' % (r.node_id, r.node_type)
                        for r in graph.node_set.all()]
        return HttpResponse(simplejson.dumps(results))


def get_node_and_neighbourhood(graph_id, node_id):
    graph = {"nodes": {}, "edges": {}}
    gdb = get_graphdb_connection(GRAPHDB_HOST)
    node = gdb.node[int(node_id)]
    properties = node.properties
    graph["nodes"][properties['_slug']] = properties
    relationships = node.relationships.all()
    edges_counter = 0
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
    graph = GraphDB.objects.get(pk=graph_id)
    if not graph.public and \
            not request.user.has_perm('schema.%s_can_see' % graph.name):
        return unauthorized_user(request)
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
    idx = gdb.nodes.indexes.get('sylva_nodes')
    result = filter_by_property(idx.get('_slug')[node_id],
                                '_type', node_type)
    result = filter_by_property(result, '_graph', graph_id)
    return result[0] if len(result) == 1 else None


def expand_node(request, graph_id):
    graph = GraphDB.objects.get(pk=graph_id)
    if not graph.public and \
            not request.user.has_perm('schema.%s_can_see' % graph.name):
        return HttpResponse(simplejson.dumps({'success': False}))
    node = get_node_from_index(request, graph_id)
    if node:
        new_graph = get_node_and_neighbourhood(graph_id, node.id)
        response_dictionary = {'success': True,
                                'new_gdata': new_graph}
    else:
        response_dictionary = {'success': False}
    return HttpResponse(simplejson.dumps(response_dictionary))


def open_node_info(request, graph_id):
    graph = GraphDB.objects.get(pk=graph_id)
    if not graph.public and \
            not request.user.has_perm('schema.%s_can_see' % graph.name):
        return HttpResponse(simplejson.dumps({'success': False}))
    else:
        node = get_node_from_index(request, graph_id)
        return HttpResponse(simplejson.dumps({'success': True,
                                            'node_id': node.id}))


def handle_csv_file(uploaded_file, separator, text_separator):
    csv_info = csv.reader(uploaded_file,
                            delimiter=str(separator),
                            quotechar=str(text_separator))
    return list(csv_info)


def import_manager(request, graph_id):
    graph = GraphDB.objects.get(pk=graph_id)
    if not request.user.has_perm('schema.%s_can_add_data' % graph.name):
        return unauthorized_user(request)
    if request.method == 'POST':
        form = UploadCSVForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                rows = handle_csv_file(request.FILES['csv_file'],
                                form.cleaned_data['separator'],
                                form.cleaned_data['text_separator'])
                row_length = len(rows[0])
            except:
                error = 'There was a problem processing your file'
                return render_to_response('graphgamel/csv/upload.html', {
                                                        'form': form,
                                                        'graph_id': graph_id,
                                                        'error_message':error})
            node_types = [n.name for n in graph.nodetype_set.all()]
            valid_relations = []
            for vr in ValidRelation.objects.filter(graph=graph):
                valid_relations.append({'node_from': vr.node_from.name,
                                        'relation': vr.relation.name,
                                        'node_to': vr.node_to.name})
            return render_to_response('graphgamel/csv/manager.html', {
                        'rows': rows,
                        'json_data': simplejson.dumps(rows),
                        'len': range(row_length),
                        'graph_id': graph_id,
                        'node_types': node_types,
                        'relations': valid_relations,
                        'valid_relations': simplejson.dumps(valid_relations)})
    else:
        form = UploadCSVForm()
    return render_to_response('graphgamel/csv/upload.html', {
                                        'form': form,
                                        'graph_id': graph_id})


def add_node_ajax(request, graph_id):
    graph = GraphDB.objects.get(pk=graph_id)
    if not request.user.has_perm('schema.%s_can_add_data' % graph.name):
        return unauthorized_user(request)
    if request.method == 'GET':
        gdb = neo4jclient.GraphDatabase(GRAPHDB_HOST)
        tmp_node = simplejson.loads(request.GET['json_node'])
        collapse = simplejson.loads(request.GET['collapse'])
        node = get_internal_attributes(tmp_node['id'],
                                        tmp_node['type'],
                                        graph_id,
                                        request.user)
        if collapse:
            new_node = get_or_create_node(gdb, node, graph)
        else:
            new_node = create_node(gdb, node, graph)
        if new_node:
            success = True
        else:
            success = False
        return HttpResponse(simplejson.dumps({'success': success}))


def add_relationship_ajax(request, graph_id):
    graph = GraphDB.objects.get(pk=graph_id)
    if not request.user.has_perm('schema.%s_can_add_data' % graph.name):
        return unauthorized_user(request)
    if request.method == 'GET':
        gdb = neo4jclient.GraphDatabase(GRAPHDB_HOST)
        relation_info = simplejson.loads(request.GET['json_relation'])
        node_from = {}
        node_to = {}
        node_from['_slug'] = relation_info['node_from']
        node_from['_type'] = relation_info['node_from_type']
        node_to['_slug'] = relation_info['node_to']
        node_to['_type'] = relation_info['node_to_type']
        if not graph.is_valid_relationship(node_from['_type'],
                                        relation_info['relation'],
                                        node_to['_type']):
            error_msg = 'Relation invalid for %s graph' % graph.name
            return HttpResponse(simplejson.dumps({'error': error_msg}))
        relation_data = relation_info['data']
        node1 = get_or_create_node(gdb, node_from, graph)
        node2 = get_or_create_node(gdb, node_to, graph)
        rel_obj = get_or_create_relationship(gdb,
                                            node1,
                                            node2,
                                            relation_info['relation'])
        if rel_obj:
            set_relationship_properties(gdb,
                            rel_obj,
                            relation_info['relation'],
                            graph_id,
                            request.user)
            for key, value in relation_data.iteritems():
                rel_obj.set(key, value)
            success = True

        else:
            success = False
        return HttpResponse(simplejson.dumps({'success': success}))


def json_to_gexf(request, json_graph):
    response = HttpResponse(mimetype='application/xml')
    response['Content-Disposition'] = 'attachment; filename=graph.gexf'
    gephi_format = converters.json_to_gexf(json_graph)
    response.write(gephi_format)
    return response


def export_graph(conversion_function, graph_id, ext):
    response = HttpResponse(mimetype='application/gml')
    response['Content-Disposition'] = 'attachment; filename=graph.%s' % ext
    graph = get_whole_graph(graph_id)
    response_data = conversion_function(graph)
    response.write(response_data)
    return response


def export_to_gml(request, graph_id):
    conversion_function = converters.neo4j_to_gml
    return export_graph(conversion_function, graph_idi, 'gml')


def export_to_gexf(request, graph_id):
    conversion_function = converters.neo4j_to_gexf
    return export_graph(conversion_function, graph_id, 'gexf')


def get_whole_graph(graph_id):
    gdb = get_graphdb_connection(GRAPHDB_HOST)
    graph = {}
    idxn = gdb.nodes.indexes.get('sylva_nodes')
    idxr = gdb.relationships.indexes.get('sylva_relationships')
    graph['nodes'] = idxn.get('_graph')[graph_id]
    graph['relationships'] = idxr.get('_graph')[graph_id]
    return graph


def visualize_all(request, graph_id):
    graph = GraphDB.objects.get(pk=graph_id)
    if not graph.public and \
            not request.user.has_perm('schema.%s_can_see' % graph.name):
        return unauthorized_user(request)
    gdb = neo4jclient.GraphDatabase(GRAPHDB_HOST)
    idx = gdb.nodes.indexes.get('sylva_nodes')
    result = idx.get('_graph')[graph_id]
    graph = {"nodes": {}, "edges": {}}
    edges = set()
    for node in result:
        graph["nodes"][node.properties['_slug']] = node.properties
        for r in node.relationships.all():
            edges.add((r.start['_slug'], r.type, r.end['_slug']))
    for i, edge in enumerate(edges):
        graph["edges"][i] = {'node1': edge[0],
                                    'node2': edge[2],
                                    'id': edge[1]}
    return render_to_response('graphgamel/graphview/explorer.html',
                                    RequestContext(request, {
                                    'json_graph': simplejson.dumps(graph),
                                    'graph_id': graph_id}))


def delete_graph_data(graph):
    gdb = neo4jclient.GraphDatabase(GRAPHDB_HOST)
    idx = gdb.nodes.indexes.get('sylva_nodes')
    result = idx.get('_graph')[graph.id]
    for node in result:
        delete_sylva_node(graph, node)


##############
# Data nodes #
##############

def data_node_add(request, graph_id, nodetype_id):
    graph = GraphDB.objects.get(pk=graph_id)
    nodetype = NodeType.objects.get(pk=nodetype_id)
    if not graph.public and \
            not request.user.has_perm('schema.%s_can_see' % graph.name):
        return unauthorized_user(request)
    gdb = neo4jclient.GraphDatabase(GRAPHDB_HOST)
    form = get_form_for_nodetype(nodetype, gdb=gdb)
    node_form = form()
    if request.POST:
        data = request.POST.copy()
        node_form = form(data)
        if node_form.is_valid():
            node_form.save()
            redirect_url = reverse("graph_data", args=[graph.id])
            return HttpResponseRedirect(redirect_url)
    return render_to_response('graph_data_node_add.html',
                              {'graph': graph,
                               'nodetype': nodetype,
                               'node_form': node_form},
                              context_instance=RequestContext(request))


def data_node_edit(request, graph_id, nodetype_id, node_id):
    graph = GraphDB.objects.get(pk=graph_id)
    if not graph.public and \
            not request.user.has_perm('schema.%s_can_see' % graph.name):
        return unauthorized_user(request)
    return render_to_response('graph_data_node_edit.html',
                              {},
                              context_instance=RequestContext(request))
