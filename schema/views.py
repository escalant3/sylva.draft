from django.contrib.auth.models import Permission
from django.core.urlresolvers import reverse
from django.db import IntegrityError
from django.shortcuts import (render_to_response,
                                redirect)
from django.template import defaultfilters
from graph.views import unauthorized_user, index
from schema.forms import CreateGraphForm, CreateDefaultProperty, EditGraphForm
from schema.models import (GraphDB, NodeType, EdgeType,
                            ValidRelation, PERMISSIONS,
                            NodeDefaultProperty, EdgeDefaultProperty)


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
    slug = defaultfilters.slugify(request.POST.get('nodetype', None))
    if slug:
        node_type = NodeType(name=slug, graph=graph)
        try:
            node_type.save()
        except IntegrityError:
            pass
    return redirect(schema_editor, graph_id)


def add_edge_type(request, graph_id):
    graph = GraphDB.objects.get(pk=graph_id)
    if not request.user.has_perm("schema.%s_can_edit_schema" % graph.name):
        return unauthorized_user(request) 
    slug = defaultfilters.slugify(request.POST.get('edgetype', None))
    if slug:
        edge_type = EdgeType(name=slug, graph=graph)
        try:
            edge_type.save()
        except IntegrityError:
            pass
    return redirect(schema_editor, graph_id)


def add_valid_relationship(request, graph_id):
    graph = GraphDB.objects.get(pk=graph_id)
    if not request.user.has_perm("schema.%s_can_edit_schema" % graph.name):
        return unauthorized_user(request) 
    node_from = NodeType.objects.filter(name=request.POST['node_from'])[0]
    edge_type = EdgeType.objects.filter(name=request.POST['relation'])[0]
    node_to = NodeType.objects.filter(name=request.POST['node_to'])[0]
    results = ValidRelation.objects.filter(node_from=node_from,
                        relation=edge_type,
                        node_to=node_to,
                        graph=graph)
    if not results:
        vr = ValidRelation(node_from=node_from,
                        relation=edge_type,
                        node_to=node_to,
                        graph=graph)
        vr.save()
    return redirect(schema_editor, graph_id)


def add_graph(request):
    if not request.user.has_perm("schema.add_graphdb"):
        return unauthorized_user(request) 
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
    return render_to_response('graphgamel/graph_manager/graph.html',
                            {'form': form,
                            'form_title': 'Create new graph',
                            'action': reverse('schema.views.add_graph')})


def edit_graph(request, graph_id):
    graph = GraphDB.objects.get(pk=graph_id)
    if not request.user.has_perm("schema.%_edit_schema"):
        return unauthorized_user(request)
    if request.method == "POST":
        form = EditGraphForm(request.POST)
        if form.is_valid():
            graph.description = form.cleaned_data['description']
            graph.public = form.cleaned_data['public']
            graph.save_changes()
            return redirect(index)
    else:
        form = EditGraphForm({'description': graph.description,
                                'public': graph.public})
    return render_to_response('graphgamel/graph_manager/graph.html',
                            {'form': form,
                            'form_title': 'Edit graph properties',
                            'action': reverse('schema.views.edit_graph',
                                            args=[graph_id])})




def delete_graph(request, graph_id):
    graph = GraphDB.objects.get(pk=graph_id)
    if not request.user.has_perm("schema.%s_can_delete" % graph.name):
        return unauthorized_user(request) 
    graph.delete()
    return redirect(index)
   

def add_default_node_property(request, graph_id, node_id):
    graph = GraphDB.objects.get(pk=graph_id)
    node = NodeType.objects.get(pk=node_id)
    if not request.user.has_perm("schema.%s_can_edit_schema" % graph.name):
        return unauthorized_user(request) 
    if request.method == "POST":
        form = CreateDefaultProperty(request.POST)
        if form.is_valid():
            ndp = NodeDefaultProperty(key=form.cleaned_data['key'],
                                        value=form.cleaned_data['value'],
                                        node=node)
            ndp.save()
            return redirect(schema_editor, graph_id)
    else:
        form = CreateDefaultProperty()
    return render_to_response('graphgamel/graph_manager/add_ndp.html', {
                                'form': form,
                                'graph_id': graph_id,
                                'node': node})


def add_default_edge_property(request, graph_id, edge_id):
    graph = GraphDB.objects.get(pk=graph_id)
    edge = EdgeType.objects.get(pk=edge_id)
    if not request.user.has_perm("schema.%s_can_edit_schema" % graph.name):
        return unauthorized_user(request) 
    if request.method == "POST":
        form = CreateDefaultProperty(request.POST)
        if form.is_valid():
            edp = EdgeDefaultProperty(key=form.cleaned_data['key'],
                                        value=form.cleaned_data['value'],
                                        edge=edge)
            edp.save()
            return redirect(schema_editor, graph_id)
    else:
        form = CreateDefaultProperty()
    return render_to_response('graphgamel/graph_manager/add_edp.html', {
                                'form': form,
                                'graph_id': graph_id,
                                'edge': edge})


def delete_default_node_property(request, graph_id, property_id):
    graph = GraphDB.objects.get(pk=graph_id)
    if not request.user.has_perm("schema.%s_can_edit_schema" % graph.name):
        return unauthorized_user(request) 
    node_default_property = NodeDefaultProperty.objects.get(pk=property_id)
    node_default_property.delete()
    return redirect(schema_editor, graph_id)


def delete_default_edge_property(request, graph_id, property_id):
    graph = GraphDB.objects.get(pk=graph_id)
    if not request.user.has_perm("schema.%s_can_edit_schema" % graph.name):
        return unauthorized_user(request) 
    edge_default_property = EdgeDefaultProperty.objects.get(pk=property_id)
    edge_default_property.delete()
    return redirect(schema_editor, graph_id)
