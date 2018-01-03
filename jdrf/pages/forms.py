from django import forms
from django.core.validators import RegexValidator


class UploadForm(forms.Form):
    file = forms.FileField()


class NewProjectForm(forms.Form):
    """Django representation of a form when a user adds a new project for
    metadata and sequence file uploads."""
    alphanumeric = RegexValidator(r'^[0-9A-Z]*$',
                                 'Only capitalized alphanumeric characters are allowed.')
    envo_term = RegexValidator(r'^ENVO:\d+', 'Must be a valid ENVO ontology term (e.x. ENVO:00000428')

    ## Required Fields
    study_id = forms.CharField(max_length=60, verbose_name='Study ID')
    pi_name = forms.CharField(max_length=80, verbose_name='PI Name')

    ## Optional fields
    sample_type = forms.ChoiceField(choices=(('mgx', 'Metagenomic'),
                                             ('16s', '16S'),
                                             ('mtx', 'Metatranscriptomic')),
                                    required=False,
                                    verbose_name='Sample Type')
    tissue = forms.CharField(max_length=60, required=False, verbose_name='Tissue (OPTIONAL)')
    geo_loc_name = forms.CharField(max_length=100, required=False, 
                                   verbose_name='Geolocation Name (OPTIONAL)')
    bioproject_accession = forms.CharField(max_length=50, required=False, 
                                           verbose_name='BioProject Accession (OPTIONAL)',
                                           validators=[alphanumeric])
    animal_vendor = forms.CharField(max_length=120, required=False, verbose_name='Animal Vendor (OPTIONAL)')
    env_biom = forms.CharField(max_length=40, required=False, 
                               verbose_name='ENVO Biom (OPTIONAL)',
                               validators=[envo_term])
    env_feature = forms.CharField(max_length=40, required=False,
                                  verbose_name='ENVO Feature (OPTIONAL)',
                                  validators=[envo_term])
    env_material = forms.CharField(max_length=40, required=False,
                                   verbose_name='ENVO Material (OPTIONAL)',
                                   validators=[envo_term])


    def clean_tissue(self):
        tissue = self.cleaned_tissue['tissue']

        if not tissue.startswith('BTO'):
            raise forms.ValidationError("Tissue must be in BRENDA ontology format (e.x. BTO_0002789)")

        return tissue            