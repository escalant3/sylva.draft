from django import forms
from graph.models import GraphDB


class CreateGraphForm(forms.Form):
    name = forms.SlugField()
    description = forms.CharField()
    public = forms.BooleanField(required=False)
