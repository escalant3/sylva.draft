import neo4jclient
import simplejson

from django.core.management.base import BaseCommand

from graph.models import Neo4jGraph
from graph.views import get_or_create_node, \
                        get_or_create_relationship

class Command(BaseCommand):

    help = """Imports data from a Sylva file."""

    def handle(self, *args, **options):
        if len(args) < 2:
            print "Usage: python manage.py importer FILE DESTINATIO_GRAPH"
            return
        else:
            graph = Neo4jGraph.objects.filter(name=args[1])
            if len(graph) == 0:
                print "Database not found"
                return
            elif len(graph) > 1:
                print "Duplicate database error"
                return 
            else:
                graph = graph[0]
            gdb = neo4jclient.GraphDatabase(graph.host)
            f = open(args[0], 'r')
            json_data = f.read()
            f.close()
            data = simplejson.loads(json_data)
            for node in data['nodes']:
                try:
                    get_or_create_node(gdb, node, graph)
                except:
                    print 'There was a problem creating one node: %s' % node
            for node1, node2, edge_type in data['edges']:
                try:
                    neonode1 = get_or_create_node(gdb, node1, graph)
                    neonode2 = get_or_create_node(gdb, node2, graph)
                    get_or_create_relationship(neonode1, neonode2, edge_type)
                except:
                    print "There was a problem with (%s,%s,%s)" % (node1,
                                                                    node2,
                                                                    edge_type)
            print "Done."
