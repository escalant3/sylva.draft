import unittest
from schema.models import Schema, NodeType, EdgeType, ValidRelation


class SchemaCreatorTestCase(unittest.TestCase):

    def setUp(self):
        self.node_team = NodeType.objects.create(name="Team")
        self.node_player = NodeType.objects.create(name="Player")
        self.node_competition = NodeType.objects.create(name="Competition")
        self.relation_takes_part_in = EdgeType.objects.create(name="TAKES_PART_IN")
        self.relation_plays_in = EdgeType.objects.create(name="PLAYS_IN")

    def testCreateValidRelationShips(self):
        self.relation1 = ValidRelation.objects.create(node_from=self.node_team,
                                            relation=self.relation_takes_part_in,
                                            node_to=self.node_competition)
        self.relation1 = ValidRelation.objects.create(node_from=self.node_player,
                                            relation=self.relation_plays_in,
                                            node_to=self.node_team)
