from django import forms
from django.utils.translation import gettext as _

from graph.utils import create_node


def get_form_for_nodetype(nodetype, gdb=False):
    fields = {}
    # Slug creation
    field_attrs = {
        "required": True,
        "label": u"* %s:" % _(u"Slug"),
        "help_text": _(u"The slug field allows to index que node for searching"),
    }
    fields["_slug"] = forms.CharField(**field_attrs)
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
        for relationship in nodetype.get_edges():
            graph_id = nodetype.graph.id
            idx = gdb.nodes.indexes.get('sylva_nodes')
            results = idx.get("_type")[nodetype.name]
            choices = [(n.id, n.properties.get("_slug")) for n in results
                       if n.properties["_graph"] == graph_id]
            label = relationship.relation.name.replace("-", " ") \
                    .replace("_", " ")
            label = "%s:" % label.capitalize()
            # TODO: Fix the required value rendering
            if node_property.required:
                label = "* %s" % label
            if relationship.arity > 0:
                help_text = _(u"Check %s elements at most." \
                              % relationship.arity)
            else:
                help_text = _(u"Check any number of elements.")
            field = forms.MultipleChoiceField(choices=choices, required=False,
                                              help_text=help_text, label=label)
            fields[relationship.relation.name] = field

    def save_form(self, *args, **kwargs):
        properties = {}
        node_properties = nodetype.nodeproperty_set.all().values("key")
        keys =  [p["key"] for p in node_properties]
        for key in keys:
            if key in self.data and len(self.data[key]) > 0:
                properties[key] = self.data[key]
            properties["_slug"] = self.data["_slug"]
            properties["_type"] = nodetype.name
            properties["_graph"] = unicode(nodetype.graph.id)
        node = create_node(gdb, properties, nodetype.graph)
        if node:
            # Create relationships only if everything was OK with node creation
            pass
    fields["save"] = save_form
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
