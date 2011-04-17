from schema.models import GraphDB, NodeType, EdgeType, ValidRelation, \
                            NodeProperty, EdgeProperty
from django.contrib import admin

class NodePropertyInline(admin.TabularInline):
    model = NodeProperty

class NodeTypeAdmin(admin.ModelAdmin):
    inlines = [NodePropertyInline]

class EdgePropertyInline(admin.TabularInline):
    model = EdgeProperty

class EdgeTypeAdmin(admin.ModelAdmin):
    inlines = [EdgePropertyInline]

class ValidRelationAdmin(admin.ModelAdmin):
    list_filter = ['graph']

admin.site.register(GraphDB)
admin.site.register(NodeType, NodeTypeAdmin)
admin.site.register(EdgeType, EdgeTypeAdmin)
admin.site.register(ValidRelation, ValidRelationAdmin)
