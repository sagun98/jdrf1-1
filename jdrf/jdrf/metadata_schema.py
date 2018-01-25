from pandas_schema import Column, Schema
from pandas_schema.validation import (LeadingWhitespaceValidation, TrailingWhitespaceValidation, 
                                      CanConvertValidation, MatchesPatternValidation, CustomSeriesValidation,
                                      InRangeValidation, InListValidation, DateFormatValidation)


study_schema = Schema([
    Column('study_id', [CustomSeriesValidation(lambda x: ~x.isnull(), 'A value is required for the study_id column.') &
                        ~InListValidation([''])]),
    Column('pi_name', [CustomSeriesValidation(lambda x: ~x.isnull(), 'A value is required for the pi_name column.') &
                        ~InListValidation([''])]),
    Column('sample_type', [InListValidation(['', 'MGX', 'MTX', '16S'])]),
    Column('geo_loc_name', [InListValidation(['']) | MatchesPatternValidation(r'\w+:\w+:\w+')]),
    Column('host_tissue_sampled', [InListValidation(['']) | MatchesPatternValidation(r'BTO_\d+')])
])

sample_schema = Schema([
    Column('animal_vendor', [LeadingWhitespaceValidation()]),
    Column('host_subject_id', [MatchesPatternValidation(r'\w+', message='Host Subject ID may only contain alphanumeric characters.')]),
    Column('host_diet', [LeadingWhitespaceValidation()]),
    Column('source_material_id', [LeadingWhitespaceValidation()]),
    Column('ethnicity', [CanConvertValidation(str, message='Ethnicity may only contain alphanumeric characters.')]),
    Column('host_family_relationship', [LeadingWhitespaceValidation()]),
    Column('host_genotype', [MatchesPatternValidation(r'^https', message='Host Genotype may only be a valid URL to the associated DbGap project.')]),
    Column('isolation_source', [LeadingWhitespaceValidation()]),
    Column('samp_mat_process', [LeadingWhitespaceValidation()]),
    Column('bioproject_accession', [InListValidation(['']) |
                                    MatchesPatternValidation(r'PRJNA\d+', message='BioProject accession must be in format \'PRJNA<NUMBERS>\'')]),
    Column('env_biom', [MatchesPatternValidation(r'ENVO:\d+')]),
    Column('env_feature', [MatchesPatternValidation(r'ENVO:\d+')]),
    Column('env_material', [MatchesPatternValidation(r'ENVO:\d+')]),
    Column('filename', [CustomSeriesValidation(lambda x: ~x.isnull(), 'A value is required for the filename column.'),
                        MatchesPatternValidation(r'\w+.[fastq|fasta|fq](.gz)?', message='Filename must be a valid fasta/fastq file with the following supported extensions: .fasta.gz, .fastq.gz, fq.gz')]),
    Column('sample_id', [CustomSeriesValidation(lambda x: ~x.isnull(), 'A value is required for the sample_id column.')]),
    Column('collection_date', [CustomSeriesValidation(lambda x: ~x.isnull(), 'A value is required for the collection_date column.'),
                               DateFormatValidation('%Y-%m-%d', message='Collection date must be in YYYY-MM-DD date format.')]),
    Column('subject_tax_id', [MatchesPatternValidation(r'\d+')]),
    Column('subject_age', [CustomSeriesValidation(lambda x: ~x.isnull(), 'A value is required for the subject_age column.'),
                           InRangeValidation(0, 120)]),
    Column('subject_sex', [CustomSeriesValidation(lambda x: ~x.isnull(), 'A value is required for the subject_sex column.'),
                           InListValidation(['M', 'F'])]),
    Column('md5_checksum', [CustomSeriesValidation(lambda x: ~x.isnull(), 'A value is required for the pi_name column.'),
                            MatchesPatternValidation(r'[a-zA-Z0-9]{32}', message='MD5 Checksum may only contain 32 alphanumeric characters.')]),
    Column('host_body_mass_index', [CanConvertValidation(float)]),
    Column('host_disease', [MatchesPatternValidation(r'DOID:\d+', message='Must provide a valid Disease Ontology ID in format \'DOID:<NUMBERS>\'')]),
    Column('variable_region', [CustomSeriesValidation(lambda x: ~x.isnull(), '') |
                               MatchesPatternValidation(r'(V[1-9],?)+', message='Variable region must be a valid 16S hypervariable region.')]),
    Column('gastrointest_disord', [CanConvertValidation(int)]),
    Column('host_body_product', [MatchesPatternValidation(r'GENEPIO_\d+', message='Must provide a valid Genetic epidemiology ontology ID in format \'GENEPIO_<NUMBERS>\'')]),
    Column('host_phenotype', [CanConvertValidation(int)]),
    Column('ihmc_medication_code', [CustomSeriesValidation(lambda x: ~x.isnull(), '') |
                                    MatchesPatternValidation(r'(\d+,?)+]', message='IHMC medication code must be a number.')]),
    Column('organism_count', [CustomSeriesValidation(lambda x: ~x.isnull(), '') |
                              InRangeValidation(1, message='Organism count must be a positive number.')]),
    Column('samp_store_dur', [InRangeValidation(1, message='Sample storage duration must be a positive number.')]),
    Column('samp_store_temp', [CanConvertValidation(int, message='Sample storage temperature must be a valid temperature number.')]),
    Column('samp_vol_mass', [MatchesPatternValidation(r'\d+[.]?\d*(g|ml)', message='Sample volume mass must be in format <NUMBER>g or <NUMBER>ml')]),
    Column('sequencer', [InListValidation(["Illumina MiSeq", "Illumina NextSeq",
                                           "Illumina HiSeq", "Illumina HiSeq X",
                                           "PacBio Sequel", "Nanopore MinION",
                                           "Nanopore PromethION", "Nanopore SmidgION",
                                           "454", "Sanger"])]),
    Column('read_number', [InRangeValidation(1, message='Read number must be a positive number.')]),
    Column('sequencing_facility', [LeadingWhitespaceValidation()])
])

schemas = {'sample': sample_schema, 'study': study_schema}