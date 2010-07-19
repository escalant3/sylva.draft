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

    def __unicode__(self):
        return self.name

class Node(models.Model):
    node_id = models.CharField(max_length=100)
    node_type = models.CharField(max_length=100)
    graph = models.ForeignKey(Graph)

    def __unicode__(self):
        return '%s. Node %s' % (self.graph.name, self.node_id)

class Media(models.Model):
    MEDIA_TYPES = (('link', 'Link'),
                    ('image', 'Image'),
                    ('audio', 'Audio'),
                    ('video', 'Video'),
                    ('document', 'Document'))
    node = models.ForeignKey(Node)
    media_caption = models.CharField(max_length=150)
    media_type = models.CharField(max_length=20, choices=MEDIA_TYPES)
    media_file = models.FileField(upload_to='nodes_media')

    def __unicode__(self):
        return 'Media (%s Node %s) -> %s %s' % (self.node.graph.name,
                                                self.node_id,
                                                self.media_type,
                                                self.media_file)

    class Meta:
        verbose_name_plural = "Media files"

