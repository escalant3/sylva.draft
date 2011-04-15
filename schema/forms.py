from django import forms
from django.contrib.auth.models import Permission, User
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
            Permission.objects.filter(name__startswith=graph.name)
    
    user = forms.CharField(validators=[user_exists])
    permissions = forms.ModelMultipleChoiceField(queryset=None)
