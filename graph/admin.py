from graph.models import Neo4jGraph, Node, Edge
from django.contrib import admin


class NodeInline(admin.TabularInline):
    model = Node


class EdgeInline(admin.TabularInline):
    model = Edge


class GraphAdmin(admin.ModelAdmin):
    inlines = [NodeInline, EdgeInline]

admin.site.register(Neo4jGraph, GraphAdmin)
admin.site.register(Node)
admin.site.register(Edge)
