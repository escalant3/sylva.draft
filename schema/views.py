from django.contrib.auth.models import Permission
from django.shortcuts import (render_to_response,
                                redirect)
from graph.views import unauthorized_user, index
from schema.forms import CreateGraphForm
from schema.models import (GraphDB, NodeType, EdgeType,
                            ValidRelation, PERMISSIONS)


def schema_editor(request, graph_id):
    graph = GraphDB.objects.get(pk=graph_id)
    if not request.user.has_perm("schema.%s_can_edit_schema" % graph.name):
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
    if not request.user.has_perm("schema.%s_can_edit_schema" % graph.name):
        return unauthorized_user(request) 
    node_type = NodeType(name=request.POST['nodetype'],
                        graph=graph)
    node_type.save()
    return redirect(schema_editor, graph_id)


def add_edge_type(request, graph_id):
    graph = GraphDB.objects.get(pk=graph_id)
    if not request.user.has_perm("schema.%s_can_edit_schema" % graph.name):
        return unauthorized_user(request) 
    edge_type = EdgeType(name=request.POST['edgetype'],
                        graph=graph)
    edge_type.save()
    return redirect(schema_editor, graph_id)


def add_valid_relationship(request, graph_id):
    graph = GraphDB.objects.get(pk=graph_id)
    if not request.user.has_perm("schema.%s_can_edit_schema" % graph.name):
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


def add_graph(request):
    if request.method == "POST":
        form = CreateGraphForm(request.POST)
        if form.is_valid():
            graph = GraphDB(name=form.cleaned_data['name'],
                            description=form.cleaned_data['description'],
                            public=form.cleaned_data['public'])
            graph.save()
            # Add all graph permissions to graph creator
            for p in PERMISSIONS:
                permission_str = '%s_%s' % (graph.name, p)
                permission = Permission.objects.filter(name=permission_str)[0]
                permission.user_set.add(request.user)
            return redirect(index)
    else:
        form = CreateGraphForm()
    return render_to_response('graphgamel/graph_manager/create.html',
                            {'form': form})
