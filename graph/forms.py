from django import forms
from graph.models import GraphDB


class UploadCSVForm(forms.Form):
    GRAPHS = [(s.id, s.name) for s in GraphDB.objects.all()]
    graph = forms.ChoiceField(choices=GRAPHS)
    csv_file = forms.FileField()
