from graph.models import Neo4jGraph, Node, Media, GraphIndex
from django.contrib import admin


class MediaInline(admin.TabularInline):
    model = Media


class NodeAdmin(admin.ModelAdmin):
    fields = ['node_id', 'node_type']
    list_filter = ['graph']
    inlines = [MediaInline]

admin.site.register(Neo4jGraph)
admin.site.register(Node, NodeAdmin)
admin.site.register(GraphIndex)
