from django import forms
<<<<<<< HEAD
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from graph.models import GraphDB
from schema.models import SylvaPermission
=======
from django.forms import widgets
from django.contrib.auth.models import Permission, User
from django.core.exceptions import ValidationError

from schema.models import (GraphDB, NodeType, NodeProperty, EdgeType,
                          EdgeProperty)
>>>>>>> Revamping the schema editor


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
