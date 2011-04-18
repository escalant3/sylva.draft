from django import forms
#from graph.models import GraphDB


def get_form_for_nodetype(nodetype, gdb=False):
    fields = {}
    # Node properties
    for node_property in nodetype.nodeproperty_set.all():
        datatype_dict = node_property.get_datatype_dict()
        label = node_property.key.replace("-", " ").replace("_", " ")
        label = "%s:" % label.capitalize()
        # TODO: Fix the required value rendering
        if node_property.required:
            label = "* %s" % label
        field_attrs = {
            "required": node_property.required,
            "initial": node_property.default,
            "label": label,
            "help_text": node_property.description,
        }
        if node_property.datatype == datatype_dict["date"]:
            field = forms.DateTimeField(**field_attrs)
        elif node_property.datatype == datatype_dict["boolean"]:
            field = forms.BooleanField(**field_attrs)
        elif node_property.datatype == datatype_dict["number"]:
            field = forms.FloatField(**field_attrs)
        else:
            field = forms.CharField(**field_attrs)
        fields[node_property.key] = field
    # Relationships
    # TODO: Use formsets to be able to add properties to the relationships
    if gdb:
        field = forms.ModelChoiceField()
    # Using an anonymous class
    form = type("%sForm" % str(nodetype.name.capitalize()),
                (forms.Form, ), fields)
    return form


class UploadCSVForm(forms.Form):
    csv_file = forms.FileField()
    separator = forms.ChoiceField(choices=[(',', ','),
                                            (';', ';'),
                                            ('\t', 'tab')])
    text_separator = forms.ChoiceField(choices=[('"', '"'),
                                                ('\'', '\'')])
