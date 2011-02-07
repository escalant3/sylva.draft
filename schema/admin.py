from schema.models import Schema, NodeType, EdgeType, ValidRelation, \
                            NodeDefaultProperty, EdgeDefaultProperty
from django.contrib import admin

class NodeDefaultPropertyInline(admin.TabularInline):
    model = NodeDefaultProperty

class EdgeDefaultPropertyInline(admin.TabularInline):
    model = EdgeDefaultProperty

class ValidRelationAdmin(admin.ModelAdmin):
    list_filter = ['schema']

admin.site.register(Schema)
admin.site.register(NodeType)
admin.site.register(EdgeType)
admin.site.register(ValidRelation, ValidRelationAdmin)
