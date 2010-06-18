import neo4jclient
import simplejson

from django.shortcuts import render_to_response, redirect

from graph.models import Graph


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
        gdb = request.session.get('gdb', None)
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
            request.session['gdb'] = gdb
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
