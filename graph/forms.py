from django import forms
from graph.models import GraphDB


class UploadCSVForm(forms.Form):
    csv_file = forms.FileField()
