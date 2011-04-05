from django.shortcuts import (render_to_response,
                                redirect)
from graph.views import unauthorized_user
from schema.models import GraphDB, NodeType, EdgeType, ValidRelation


def schema_editor(request, graph_id):
    graph = GraphDB.objects.get(pk=graph_id)
    if not request.user.has_perm("%s_can_edit_schema" % graph.name):
        return unauthorized_user(request) 
    node_types = graph.nodetype_set.all()
    edge_types = graph.edgetype_set.all()
    valid_relationships = graph.validrelation_set.all()
    return render_to_response('graphgamel/graph_manager/editor.html', {
                                'graph_id': graph_id,
                                'node_types': node_types,
                                'edge_types': edge_types,
                                'valid_relationships': valid_relationships})


def add_node_type(request, graph_id):
    graph = GraphDB.objects.get(pk=graph_id)
    if not request.user.has_perm("%s_can_edit_schema" % graph.name):
        return unauthorized_user(request) 
    node_type = NodeType(name=request.POST['nodetype'],
                        graph=graph)
    node_type.save()
    return redirect(schema_editor, graph_id)


def add_edge_type(request, graph_id):
    graph = GraphDB.objects.get(pk=graph_id)
    if not request.user.has_perm("%s_can_edit_schema" % graph.name):
        return unauthorized_user(request) 
    edge_type = EdgeType(name=request.POST['edgetype'],
                        graph=graph)
    edge_type.save()
    return redirect(schema_editor, graph_id)


def add_valid_relationship(request, graph_id):
    graph = GraphDB.objects.get(pk=graph_id)
    if not request.user.has_perm("%s_can_edit_schema" % graph.name):
        return unauthorized_user(request) 
    node_from = NodeType.objects.filter(name=request.POST['node_from'])[0]
    edge_type = EdgeType.objects.filter(name=request.POST['relation'])[0]
    node_to = NodeType.objects.filter(name=request.POST['node_to'])[0]
    vr = ValidRelation(node_from=node_from,
                        relation=edge_type,
                        node_to=node_to,
                        graph=graph)
    vr.save()
    return redirect(schema_editor, graph_id)
