# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class JDFRProject(models.Model):
    """Object representation of a JDRF project."""
    user = models.ForeignKey(User)

    study_id = models.CharField(max_length=60)
    pi_name = models.CharField(max_length=80)

    sample_type = models.CharField(max_length=3, 
                                   choices=(('mgx', 'Metagenomic'),
                                            ('16s', '16S'),
                                            ('mtx', 'Metatranscriptomic')),
                                   blank=True, null=True)
    tissue = models.CharField(max_length=60, blank=True, null=True)
    geo_loc_name = models.CharField(max_length=100, blank=True, null=True)
    bioproject_accession = models.CharField(max_length=50, blank=True, null=True)
    animal_vendor = models.CharField(max_length=120, blank=True, null=True)
    env_biom = models.CharField(max_length=40, blank=True, null=True)
    env_feature = models.CharField(max_length=40, blank=True, null=True)
    env_material = models.CharField(max_length=40, blank=True, null=True)

    def __str__(self):
        return self.study_id