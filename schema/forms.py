from django import forms
from django.core.exceptions import ValidationError
from graph.models import GraphDB


def unique_graph_name(value):
    for graph in GraphDB.objects.all():
        if graph.name == value:
            raise ValidationError(u'Graph %s already exist' % value)


class CreateGraphForm(forms.Form):
    name = forms.SlugField(validators=[unique_graph_name])
    description = forms.CharField()
    public = forms.BooleanField(required=False)


class CreateDefaultProperty(forms.Form):
    key = forms.SlugField()
    value = forms.CharField()
