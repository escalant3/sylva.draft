from django.db import models

from schema.models import Schema, NodeType, EdgeType

# Create your models here.


class Graph(models.Model):
    name = models.CharField(max_length=30)
    description = models.CharField(max_length=100)
    schema = models.ForeignKey(Schema)

    def __unicode__(self):
        return self.name


class Neo4jGraph(Graph):
    host = models.CharField(max_length=100)


class Node(models.Model):
    name = models.CharField(max_length=30)
    node_type = models.ForeignKey(NodeType)
    graph = models.ForeignKey(Graph)

    def __unicode__(self):
        return u'%s: %s' %(self.node_type, self.name)


class Edge(models.Model):
    node_from = models.ForeignKey(Node, related_name='node_from')
    edge_type = models.ForeignKey(EdgeType)
    node_to = models.ForeignKey(Node, related_name='node_to')
    graph = models.ForeignKey(Graph)

    def __unicode__(self):
        return u'%s %s %s' % (self.node_from,
                            self.edge_type,
                            self.node_to)

