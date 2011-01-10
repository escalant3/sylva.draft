from schema.models import Schema, NodeType, EdgeType, ValidRelation, \
                            NodeDefaultProperty, EdgeDefaultProperty
from django.contrib import admin

class NodeDefaultPropertyInline(admin.TabularInline):
    model = NodeDefaultProperty

class NodeTypeAdmin(admin.ModelAdmin):
    inlines = [NodeDefaultPropertyInline]
    list_filter = ['schema']

class EdgeDefaultPropertyInline(admin.TabularInline):
    model = EdgeDefaultProperty

class EdgeTypeAdmin(admin.ModelAdmin):
    inlines = [EdgeDefaultPropertyInline]
    list_filter = ['schema']

class ValidRelationAdmin(admin.ModelAdmin):
    list_filter = ['schema']

admin.site.register(Schema)
admin.site.register(NodeType, NodeTypeAdmin)
admin.site.register(EdgeType, EdgeTypeAdmin)
admin.site.register(ValidRelation, ValidRelationAdmin)
