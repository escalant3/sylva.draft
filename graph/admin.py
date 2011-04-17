from graph.models import Node, Media
from django.contrib import admin


class MediaInline(admin.TabularInline):
    model = Media


class NodeAdmin(admin.ModelAdmin):
    fields = ['node_id', 'node_type']
    list_filter = ['graph']
    inlines = [MediaInline]

admin.site.register(Node, NodeAdmin)
