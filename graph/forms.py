from django import forms
from graph.models import Neo4jGraph

GRAPHS = [(s.id, s.name) for s in Neo4jGraph.objects.all()]

class UploadCSVForm(forms.Form):
    print GRAPHS
    graph = forms.ChoiceField(choices=GRAPHS)
    csv_file = forms.FileField()
