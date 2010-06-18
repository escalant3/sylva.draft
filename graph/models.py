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
