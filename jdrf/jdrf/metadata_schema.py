from pandas_schema import Column, Schema
from pandas_schema.validation import (LeadingWhitespaceValidation, TrailingWhitespaceValidation, 
                                      CanConvertValidation, MatchesPatternValidation, CustomSeriesValidation,
                                      InRangeValidation, InListValidation, DateFormatValidation)


study_schema = Schema([
    Column('study_id', [CustomSeriesValidation(lambda x: ~x.isnull(), 'A value is required for the study_id column.') &
                        ~InListValidation([''])]),
    Column('pi_name', [CustomSeriesValidation(lambda x: ~x.isnull(), 'A value is required for the pi_name column.') &
                        ~InListValidation([''])]),
    Column('sample_type', [InListValidation(['', 'MGX', 'MTX', '16S', 'other'])]),
    Column('bioproject_accession', [InListValidation(['']) | MatchesPatternValidation(r'PRJNA\d+')]),
    Column('geo_loc_name', [InListValidation(['']) | MatchesPatternValidation(r'\w+:\w+:\w+')]),
    Column('analysis_desc', [InListValidation(['']) | CanConvertValidation(str)]),
    Column('sequencing_facility', [LeadingWhitespaceValidation()]),
    Column('env_biom', [MatchesPatternValidation(r'ENVO:\d+') | InListValidation([''])]),
    Column('env_feature', [MatchesPatternValidation(r'ENVO:\d+') | InListValidation([''])]),
    Column('env_material', [MatchesPatternValidation(r'ENVO:\d+') | InListValidation([''])]),
    Column('host_tissue_sampled', [InListValidation(['']) | MatchesPatternValidation(r'BTO:\d+')]),
    Column('animal_vendor', [LeadingWhitespaceValidation()]),
    Column('paired', [InListValidation(['yes', 'no',''])])
])

sample_schema = Schema([
    Column('host_subject_id', [MatchesPatternValidation(r'\w+', message='Host Subject ID may only contain alphanumeric characters.')]),
    Column('host_diet', [LeadingWhitespaceValidation()], allow_empty=True),
    Column('source_material_id', [LeadingWhitespaceValidation()], allow_empty=True),
    Column('ethnicity', [CanConvertValidation(str, message='Ethnicity may only contain alphanumeric characters.')], allow_empty=True),
    Column('host_family_relationship', [LeadingWhitespaceValidation()], allow_empty=True),
    Column('host_genotype', [LeadingWhitespaceValidation() |
                             MatchesPatternValidation(r'^[http|www]', message='Host Genotype may only be a valid URL to the associated DbGap project.')],
           allow_empty=True),
    Column('isolation_source', [LeadingWhitespaceValidation()], allow_empty=True), 
    Column('samp_mat_process', [LeadingWhitespaceValidation()], allow_empty=True),
    Column('filename', [CustomSeriesValidation(lambda x: ~x.isnull(), 'A value is required for the filename column.'),
                        MatchesPatternValidation(r'\w+.[fastq|fasta|fq](.gz)?', message='Filename must be a valid fasta/fastq file with the following supported extensions: .fasta.gz, .fastq.gz, fq.gz')]),
    Column('sample_id', [CustomSeriesValidation(lambda x: ~x.isnull(), 'A value is required for the sample_id column.')]),
    Column('collection_date', [CustomSeriesValidation(lambda x: ~x.isnull(), 'A value is required for the collection_date column.'),
                               DateFormatValidation('%Y-%m-%d', message='Collection date must be in YYYY-MM-DD date format.')]),
    Column('subject_tax_id', [MatchesPatternValidation(r'\d+')]),
    Column('subject_age', [CustomSeriesValidation(lambda x: ~x.isnull(), 'A value is required for the subject_age column.'),
                           InRangeValidation(0, 120)]),
    Column('subject_sex', [CustomSeriesValidation(lambda x: ~x.isnull(), 'A value is required for the subject_sex column.'),
                           InListValidation(['M', 'm', 'F', 'f'])]),
    Column('md5_checksum', [CustomSeriesValidation(lambda x: ~x.isnull(), 'A value is required for the pi_name column.'),
                            MatchesPatternValidation(r'[a-zA-Z0-9]{32}', message='MD5 Checksum may only contain 32 alphanumeric characters.')]),
    Column('host_body_mass_index', [LeadingWhitespaceValidation() | CanConvertValidation(float)], allow_empty=True),
    Column('host_disease', [LeadingWhitespaceValidation() | 
                            MatchesPatternValidation(r'DOID:\d+', message='Must provide a valid Disease Ontology ID in format \'DOID:<NUMBERS>\'')],
           allow_empty=True),
    Column('variable_region', [CustomSeriesValidation(lambda x: ~x.isnull(), '') |
                               MatchesPatternValidation(r'(V[1-9],?)+', message='Variable region must be a valid 16S hypervariable region.')],
           allow_empty=True),
    Column('gastrointest_disord', [LeadingWhitespaceValidation() | CanConvertValidation(int)], allow_empty=True),
    Column('host_body_product', [LeadingWhitespaceValidation() |
                                 MatchesPatternValidation(r'GENEPIO_\d+', message='Must provide a valid Genetic epidemiology ontology ID in format \'GENEPIO_<NUMBERS>\'')],
           allow_empty=True),
    Column('host_phenotype', [LeadingWhitespaceValidation() | CanConvertValidation(int)], allow_empty=True),
    Column('ihmc_medication_code', [CustomSeriesValidation(lambda x: ~x.isnull(), '') |
                                    MatchesPatternValidation(r'(\d+,?)+]', message='IHMC medication code must be a number.')], allow_empty=True),
    Column('organism_count', [CustomSeriesValidation(lambda x: ~x.isnull(), '') |
                              InRangeValidation(1, message='Organism count must be a positive number.')], allow_empty=True),
    Column('samp_store_dur', [LeadingWhitespaceValidation() | 
                              InRangeValidation(1, message='Sample storage duration must be a positive number.')], allow_empty=True),
    Column('samp_store_temp', [LeadingWhitespaceValidation() | 
                               CanConvertValidation(int, message='Sample storage temperature must be a valid temperature number.')], allow_empty=True),
    Column('samp_vol_mass', [LeadingWhitespaceValidation() |
                             MatchesPatternValidation(r'\d+[.]?\d*(g|ml)', message='Sample volume mass must be in format <NUMBER>g or <NUMBER>ml')], 
           allow_empty=True),
    Column('sequencer', [InListValidation(["Illumina MiSeq", "Illumina NextSeq", "illumina miseq", "illumina nextseq",
                                           "Illumina HiSeq", "Illumina HiSeq X", "illumina hiseq", "illumina hiseq x",
                                           "PacBio Sequel", "Nanopore MinION", "pacbio sequel", "nanopore minion",
                                           "Nanopore PromethION", "Nanopore SmidgION", "nanopore promethion", "nanopore smidgion",
                                           "454", "Sanger", "sanger"])]),
    Column('read_number', [LeadingWhitespaceValidation() |
                           InRangeValidation(1, message='Read number must be a positive number.')], allow_empty=True)
])

schemas = {'sample': sample_schema, 'study': study_schema}
