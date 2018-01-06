from pandas_schema import Column, Schema
from pandas_schema.validation import (LeadingWhitespaceValidation, TrailingWhitespaceValidation, 
                                      CanConvertValidation, MatchesPatternValidation, CustomSeriesValidation,
                                      InRangeValidation, InListValidation, DateFormatValidation)


study_schema = Schema([
    Column('study_id', [CustomSeriesValidation(lambda x: ~x.isnull(), 'A value is required for the study_id column.') &
                        ~InListValidation([''])]),
    Column('pi_name', [CustomSeriesValidation(lambda x: ~x.isnull(), 'A value is required for the pi_name column.') &
                        ~InListValidation([''])]),
    Column('sample_type', [CustomSeriesValidation(lambda x: ~x.isnull(), 'A value is required for the sample_type column.'),
                           InListValidation(['MGX', 'MTX', '16S'])]),
    Column('geo_loc_name', [MatchesPatternValidation(r'\w+:\w+:\w+')]),
    Column('host_tissue_sample_id', [MatchesPatternValidation(r'BTO_\d+')]),
])

sample_schema = Schema([
    Column('animal_vendor', [LeadingWhitespaceValidation()]),
    Column('host_subject_id', [LeadingWhitespaceValidation()]),
    Column('host_diet', [LeadingWhitespaceValidation()]),
    Column('source_material_id', [LeadingWhitespaceValidation()]),
    Column('ethnicity', [CanConvertValidation(str)]),
    Column('host_family_relationship', [LeadingWhitespaceValidation()]),
    Column('host_genotype', [MatchesPatternValidation(r'^https')]),
    Column('isolation_source', [LeadingWhitespaceValidation()]),
    Column('samp_mat_process', [LeadingWhitespaceValidation()]),
    Column('bioproject_accession', [CustomSeriesValidation(lambda x: ~x.isnull(), '') |
                                    MatchesPatternValidation(r'PRJNA\d+')]),
    Column('env_biom', [MatchesPatternValidation(r'ENVO:\d+')]),
    Column('env_feature', [MatchesPatternValidation(r'ENVO:\d+')]),
    Column('env_material', [MatchesPatternValidation(r'ENVO:\d+')]),
    Column('filename', [CustomSeriesValidation(lambda x: ~x.isnull(), 'A value is required for the filename column.'),
                        MatchesPatternValidation(r'\w+.fastq(.gz)?')]),
    Column('sample_id', [CustomSeriesValidation(lambda x: ~x.isnull(), 'A value is required for the sample_id column.')]),
    Column('collection_date', [CustomSeriesValidation(lambda x: ~x.isnull(), 'A value is required for the collection_date column.'),
                               DateFormatValidation('%Y-%m-%d')]),
    Column('subject_tax_id', [MatchesPatternValidation(r'\d+')]),
    Column('subject_age', [CustomSeriesValidation(lambda x: ~x.isnull(), 'A value is required for the subject_age column.'),
                           InRangeValidation(0, 120)]),
    Column('subject_sex', [CustomSeriesValidation(lambda x: ~x.isnull(), 'A value is required for the subject_sex column.'),
                           InListValidation(['M', 'F'])]),
    Column('md5_checksum', [CustomSeriesValidation(lambda x: ~x.isnull(), 'A value is required for the pi_name column.'),
                            MatchesPatternValidation(r'[a-zA-Z0-9]{32}')]),
    Column('host_body_mass_index', [CanConvertValidation(float)]),
    Column('host_disease', [MatchesPatternValidation(r'DOID:\d+')]),
    Column('variable_region', [CustomSeriesValidation(lambda x: ~x.isnull(), '') |
                               MatchesPatternValidation(r'(V[1-9],?)+')]),
    Column('gastrointest_disord', [CanConvertValidation(int)]),
    Column('host_body_product', [MatchesPatternValidation(r'GENEPIO_\d+')]),
    Column('host_phenotype', [CanConvertValidation(int)]),
    Column('ihmc_medication_code', [CustomSeriesValidation(lambda x: ~x.isnull(), '') |
                                    MatchesPatternValidation(r'(\d+,?)+]')]),
    Column('organism_count', [CustomSeriesValidation(lambda x: ~x.isnull(), '') |
                              InRangeValidation(1)]),
    Column('samp_store_dur', [InRangeValidation(1)]),
    Column('samp_store_temp', [CanConvertValidation(int)]),
    Column('samp_vol_mass', [MatchesPatternValidation(r'\d+[.]?\d*(g|ml)')]),
    Column('sequencer', [InListValidation(["Illumina MiSeq", "Illumina NextSeq",
                                           "Illumina HiSeq", "Illumina HiSeq X",
                                           "PacBio Sequel", "Nanopore MinION",
                                           "Nanopore PromethION", "Nanopore SmidgION",
                                           "454", "Sanger"])]),
    Column('read_number', [InRangeValidation(1)]),
    Column('sequencing_facility', [LeadingWhitespaceValidation()])
])