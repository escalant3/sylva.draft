import re
import simplejson
from random import randint

from django.contrib.auth.models import ContentType, Permission, User
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from django.db import models


PERMISSIONS = ('can_see', 'can_edit', 'can_delete', 'can_edit_schema',
        'can_edit_properties', 'can_edit_permissions',
        'can_add_data', 'can_edit_data', 'can_delete_data',
        'can_add_operator', 'can_edit_operator', 'can_delete_operator')


def is_alphanumeric(value):
    if not re.match(r'^\w+$', value):
        raise ValidationError(u'%s is an invalid identifier' % value)


class GraphDB(models.Model):
    name = models.SlugField(max_length=30, unique=True)
    description = models.TextField()
    public = models.BooleanField()
    order = models.IntegerField()
    owner = models.ForeignKey(User, blank=True, null=True)

    class Meta:
        unique_together = ["order", "owner"]

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        objects = self.__class__.objects
        orders = objects.all().values("order").order_by("-order")[:1]
        if orders:
            self.order = orders[0]["order"] + 1
        else:
            self.order = 1
        # Call the "real" save() method.
        super(GraphDB, self).save(*args, **kwargs)
        self.create_new_permissions()

    def save_changes(self, *args, **kwargs):
        super(GraphDB, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        super(GraphDB, self).delete(*args, **kwargs)
        # TODO Delete data from the Neo4j Database

    def create_new_permissions(self):
        new_permissions = ["%s_%s" % (self.name, p) for p in PERMISSIONS]
        content_type = ContentType.objects.filter(model='graphdb')[0]
        for np in new_permissions:
            p = SylvaPermission(content_type=content_type,
                                name=np,
                                codename=np,
                                graph=self)
            p.save()

    def get_dictionaries(self):
        form_structure = {}
        valid_relations = ValidRelation.objects.filter(graph=self)
        from_nodes = set([vr.node_from for vr in valid_relations])
        for node in from_nodes:
            form_structure[node] = {}
            form_structure[node.name] = {}
            relations = set([r.relation for r in \
                                valid_relations.filter(node_from=node)])
            for relation in relations:
                form_structure[node.name][relation.name] = {}
                to_nodes = [r.node_to.name for r in valid_relations.filter(
                                                        node_from=node,
                                                        relation=relation)]
                for to_node in to_nodes:
                    form_structure[node.name][relation.name][to_node] = {}
        for node_obj in from_nodes:
            form_structure.pop(node_obj)
        return form_structure

    def get_incoming_and_outgoing(self, node_type):
        outgoing = {}
        incoming = {}
        for vr in ValidRelation.objects.filter(graph=self):
            if vr.node_from.name == node_type:
                if not vr.relation.name in outgoing:
                    outgoing[vr.relation.name] = {}
                outgoing[vr.relation.name][vr.node_to.name] = None
            if vr.node_to.name == node_type:
                if not vr.relation.name in incoming:
                    incoming[vr.relation.name] = {}
                incoming[vr.relation.name][vr.node_from.name] = None
        return outgoing, incoming

    def get_node_types(self):
        node_types = set()
        for vr in ValidRelation.objects.filter(graph=self):
            if vr.node_from.name not in node_types:
                node_types.add(vr.node_from.name)
            if vr.node_to.name not in node_types:
                node_types.add(vr.node_to.name)
        return list(node_types)

    def get_json_schema_graph(self):
        nodes = {}
        node_types = self.get_node_types()
        for node_type in node_types:
            nodes[node_type] = {'_slug': node_type}
        edges = {}
        counter = 0
        valid_relations = self.get_dictionaries()
        for node_from_key in valid_relations:
            for relation_key in valid_relations[node_from_key]:
                for node_to_key in valid_relations[node_from_key][relation_key]:
                    edges[counter] = {'node1': node_from_key,
                                        'node2': node_to_key,
                                        '_slug': relation_key}
                    counter += 1
        return simplejson.dumps({'nodes': nodes, 'edges': edges})

    def get_node_visual_data(self):
        visual_data = {}
        node_types = self.get_node_types()
        for node in node_types:
            color = ('#%x' % randint(0, 16777216)).replace(' ', '0')
            visual_data[node] = {"color": color,
                                "size": "1.0",
                                "label": node}
        return visual_data

    def is_valid_relationship(self, node_from, edge_type, node_to):
        return ValidRelation.objects.filter(graph=self,
                                node_from__name=node_from,
                                relation__name=edge_type,
                                node_to__name=node_to)


class NodeType(models.Model):
    name = models.SlugField(max_length=30)
    graph = models.ForeignKey(GraphDB)

    def __unicode__(self):
        return "%s (%s)" % (self.name, self.graph.name)

    class Meta:
        unique_together = ('name', 'graph')


class EdgeType(models.Model):
    name = models.SlugField(max_length=30)
    graph = models.ForeignKey(GraphDB)

    def __unicode__(self):
        return "%s (%s)" % (self.name, self.graph.name)

    class Meta:
        unique_together = ('name', 'graph')


class ValidRelation(models.Model):
    node_from = models.ForeignKey(NodeType, related_name='node_from')
    relation = models.ForeignKey(EdgeType)
    node_to = models.ForeignKey(NodeType, related_name='node_to')
    graph = models.ForeignKey(GraphDB)

    def __unicode__(self):
        return '%s %s %s' % (self.node_from.name, self.relation.name, self.node_to.name)


class BaseProperty(models.Model):
    key = models.CharField(max_length=30)
    default = models.CharField(max_length=255, blank=True, null=True)
    value = models.CharField(max_length=255, blank=True)
    DATATYPE_CHOICES = (
        (u'u', _(u'Undefined')),
        (u'n', _(u'Number')),
        (u's', _(u'String')),
        (u'b', _(u'Boolean')),
        (u'd', _(u'Date')),
    )
    datatype = models.CharField(max_length=1, choices=DATATYPE_CHOICES,
                                default=u"u")
    required = models.BooleanField(default=False)
    order = models.IntegerField()

    class Meta:
        abstract = True

    def __unicode__(self):
        return "%s: %s" % (self.key, self.value)

    def save(self, *args, **kwargs):
        objects = self.__class__.objects
        orders = objects.all().values("order").order_by("-order")[:1]
        if orders:
            self.order = orders[0]["order"] + 1
        else:
            self.order = 1
        super(BaseProperty, self).save(*args, **kwargs)

    def get_datatype_dict(self):
        return dict([(v.lower(), u) for (u, v) in self.DATATYPE_CHOICES])

    def get_datatype(self):
        datatype_dict = dict(self.DATATYPE_CHOICES)
        return datatype_dict.get(self.datatype)


class NodeProperty(BaseProperty):
    node = models.ForeignKey(NodeType)

    class Meta:
        verbose_name_plural = "Node Properties"
        unique_together = ["order", "node"]


class EdgeProperty(BaseProperty):
    edge = models.ForeignKey(EdgeType)

    class Meta:
        verbose_name_plural = "Edge Properties"
        unique_together = ["order", "edge"]


class SylvaPermission(Permission):
    graph = models.ForeignKey(GraphDB)
