from django import forms
from django.validators import RegexValidator


class UploadForm(forms.Form):
    file = forms.FileField()


class NewProjectForm(forms.Form):
    """Django representation of a form when a user adds a new project for
    metadata and sequence file uploads."""
    alphanumeric = RegexValidator(r'^[0-9A-Z]*$',
                                 'Only capitalized alphanumeric characters are allowed.')
    envo_term = RegexValidator(r'^ENVO:\d+', 'Must be a valid ENVO ontology term (e.x. ENVO:00000428')

    ## Required Fields
    study_id = forms.CharField(max_length=60)
    pi_name = forms.CharField(max_length=80)

    ## Optional fields
    sample_type = forms.ChoiceField(choices=(('mgx', 'Metagenomic'),
                                             ('16s', '16S'),
                                             ('mtx', 'Metatranscriptomic')),
                                             blank=True)
    tissue = forms.CharField(max_length=60, blank=True)
    geo_loc_name = forms.CharField(max_length=100, blank=True)
    bioproject_accession = forms.CharField(max_length=50, blank=True, validators=[alphanumeric])
    animal_vendor = forms.CharField(max_length=120, blank=True)
    env_biom = forms.CharField(max_length=40, blank=True, validators=[envo_term])
    env_feature = forms.CharField(max_length=40, blank=True, validators=[envo_term])
    env_material = forms.CharField(max_length=40, blank=True, validators=[envo_term])

    def clean_tissue(self):
        tissue = self.cleaned_tissue['tissue']

        if not tissue.startswith('BTO'):
            raise forms.ValidationError("Tissue must be in BRENDA ontology format (e.x. BTO_0002789)")

        return tissue            