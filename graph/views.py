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


def editor(request, graph_id):
    messages = []
    graph = Graph.objects.get(pk=graph_id)
    schema = graph.schema
    if request.method == 'POST':
        gdb = neo4jclient.GraphDatabase(request.session['host'])
        if gdb:
            data = request.POST.copy()
            if data['mode'] == 'node':
                pass
                node = {'id': data['node_id']}
                properties = simplejson.loads(data['node_properties'])
                node.update(properties)
                node = gdb.node(**node)
                messages = ['Created %s' % (data['node_id'])]
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
                node1 = gdb.node(**node_from)
                node2 = gdb.node(**node_to)
                getattr(node1, edge_type)(node2)
                messages = ['Created %s(%s) %s %s(%s) relation' %
                                        (data['node_from_id'],
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
        request.session['form_structure'] = form_structure
    form_structure = request.session['form_structure']
    return render_to_response('graphgamel/editor.html', {
                        'schema': schema,
                        'messages': messages,
                        'form_structure': form_structure})


def info(request, graph_id, node_id):
    gdb = neo4jclient.GraphDatabase(request.session["host"])
    node = gdb.node[int(node_id)]
    properties = [(key, value) for key, value in node.properties.iteritems()]
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
    return render_to_response('graphgamel/info.html', {'properties': properties,
                                    'relationships': relationships_list})


def add_property(request, graph_id, node_id):
    if request.is_ajax():
        graph = Graph.objects.get(pk=graph_id)
        gdb = neo4jclient.GraphDatabase(graph.neo4jgraph.host)
        key = request.GET['property_key']
        value = request.GET['property_value']
        if key not in RESERVED_FIELD_NAMES:
            n = gdb.node[int(node_id)]
            if key not in n.properties.keys():
                n.set(key, value)
                return HttpResponse()
