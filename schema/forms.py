from django import forms
from django.forms import widgets
from django.contrib.auth.models import Permission, User
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from schema.models import (GraphDB, NodeType, NodeProperty, EdgeType,
                           EdgeProperty, SylvaPermission, ValidRelation)


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


class EditGraphForm(forms.Form):
    description = forms.CharField()
    public = forms.BooleanField(required=False)


def user_exists(value):
    user = User.objects.filter(username=value)
    if not user:
        raise ValidationError(u'User %s does not exist' % value)


class EditPermissionsForm(forms.Form):

    def __init__(self, *args, **kwargs):
        graph = kwargs.pop('graph', None)
        super(EditPermissionsForm, self).__init__(*args, **kwargs)
        self.fields['permissions'].queryset = \
            graph.sylvapermission_set.all()

    user = forms.CharField(validators=[user_exists])
    permissions = forms.ModelMultipleChoiceField(queryset=None)


###################################
# Schema editor form and formsets #
###################################

class NodeTypeForm(forms.ModelForm):

    class Meta:
        model = NodeType


class EdgeTypeForm(forms.ModelForm):

    class Meta:
        model = EdgeType


class NodePropertyForm(forms.ModelForm):

    class Meta:
        model = NodeProperty
        exclude = ("order", "node", "value")

    def save(self, *args, **kwargs):
        self.instance.node = self.initial["node"]
        super(NodePropertyForm, self).save(*args, **kwargs)


class EdgePropertyForm(forms.ModelForm):

    class Meta:
        model = EdgeProperty
        exclude = ("order", "edge", "value")

    def save(self, *args, **kwargs):
        self.instance.edge = self.initial["edge"]
        super(EdgePropertyForm, self).save(*args, **kwargs)


class ValidRelationForm(forms.ModelForm):
    relation = forms.CharField(help_text=_("Relation name, like 'Knows' or 'Writes'"))

    class Meta:
        model = ValidRelation
        exclude = ("node_from", "graph", "relation")

    def clean(self):
        cleaned_data = self.cleaned_data
        edge_type = self.data["relation"]
        edges = EdgeType.objects.filter(name__iexact=edge_type)
        if edges:
            cleaned_data["relation"] = edges[0]
        else:
            edge = EdgeType.objects.create(name=edge_type,
                                           graph=self.initial["graph"])
            cleaned_data["relation"] = edge
        self.initial["relation"] = cleaned_data["relation"]
        return cleaned_data

    def save(self, *args, **kwargs):
        self.instance.node_from = self.initial["node_from"]
        self.instance.relation = self.initial["relation"]
        self.instance.graph = self.initial["graph"]
        super(ValidRelationForm, self).save(*args, **kwargs)
