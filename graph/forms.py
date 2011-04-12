from django import forms
from graph.models import GraphDB


class UploadCSVForm(forms.Form):
    csv_file = forms.FileField()
    separator = forms.ChoiceField(choices=[(',',','),
                                            (';', ';'),
                                            ('\t', 'tab')])
    text_separator = forms.ChoiceField(choices=[('"', '"'),
                                                ('\'', '\'')])
