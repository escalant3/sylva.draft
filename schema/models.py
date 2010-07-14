from django.db import models

# Create your models here.


class NodeType(models.Model):
    name = models.CharField(max_length=30)

    def __unicode__(self):
        return self.name


class EdgeType(models.Model):
    name = models.CharField(max_length=30)

    def __unicode__(self):
        return self.name


class ValidRelation(models.Model):
    node_from = models.ForeignKey(NodeType, related_name='node_from')
    relation = models.ForeignKey(EdgeType)
    node_to = models.ForeignKey(NodeType, related_name='node_to')

    def __unicode__(self):
        return '%s %s %s' % (self.node_from.name, self.relation.name, self.node_to.name)


class Schema(models.Model):
    name = models.CharField(max_length=30)
    description = models.CharField(max_length=100)
    valid_relations = models.ManyToManyField(ValidRelation)

    def __unicode__(self):
        return self.name

    def get_dictionaries(self):
        form_structure = {}
        valid_relations = self.valid_relations.all()
        from_nodes = set([vr.node_from for vr in valid_relations])
        for node in from_nodes:
            form_structure[node] = {}
            form_structure[node.name] = {}
            relations = set([r.relation for r in \
                                self.valid_relations.filter(node_from=node)])
            for relation in relations:
                form_structure[node.name][relation.name] = {}
                to_nodes = [r.node_to.name for r in self.valid_relations.filter(
                                                        node_from=node,
                                                        relation=relation)]
                for to_node in to_nodes:
                    form_structure[node.name][relation.name][to_node] = {}
        for node_obj in from_nodes:
            form_structure.pop(node_obj)
        return form_structure

    def get_node_types(self):
        node_types = set();
        for vr in self.valid_relations.all():
            if vr.node_from.name not in node_types:
                node_types.add(vr.node_from.name)
            if vr.node_to.name not in node_types:
                node_types.add(vr.node_to.name)
        return list(node_types)
