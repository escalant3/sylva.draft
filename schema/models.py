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
        return '%s %s %s' % (self.node_from, self.relation, self.node_to)


class Schema(models.Model):
    name = models.CharField(max_length=30)
    description = models.CharField(max_length=100)
    valid_relations = models.ManyToManyField(ValidRelation)

    def __unicode__(self):
        return self.name
