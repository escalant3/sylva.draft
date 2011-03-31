from graph.models import GraphDB, Node, Media, GraphIndex
from django.contrib import admin


class MediaInline(admin.TabularInline):
    model = Media


class NodeAdmin(admin.ModelAdmin):
    fields = ['node_id', 'node_type']
    list_filter = ['graph']
    inlines = [MediaInline]

admin.site.register(GraphDB)
admin.site.register(Node, NodeAdmin)
admin.site.register(GraphIndex)
