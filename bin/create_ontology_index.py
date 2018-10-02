
"""
Parses a provided ontology file (in X format) and creates a Whoosh index that 
can be rapidly queried by ontology ID or names and synonyms.
"""


import argparse
import os

import pronto

from whoosh.index import create_in
from whoosh.fields import *
from whoosh.analysis import *


def parse_cli_arguments():
    """ Parses command-line arguments passed into this script """
    parser = argparse.ArgumentParser('Parses the provided ontology file and '
                                     'creates a searchable Whoosh index.')
    parser.add_argument('-i', '--input-ontology', required=True, 
                        help='Ontology to create an index out of.')
    parser.add_argument('-o', '--output-directory', required=True, 
                        help='Output directory to write Whoosh index too.')

    return parser.parse_args()


def main(args):
    print "Processing ontology file: %s" % os.path.basename(args.input_ontology)
    print "-------------------------"
    index_dir = os.path.join(args.output_directory, 'index')
    if not os.path.exists(index_dir):
        print "Index directory does not exist. Creating directory at %s" % index_dir
        os.makedirs(index_dir)
    

    ont = pronto.Ontology(args.input_ontology)
    schema = Schema(envo_id=ID(stored=True), name=NGRAMWORDS(stored=True))

    ix = create_in(index_dir, schema)
    writer = ix.writer()

    term_count = 0
    for term in ont:
        if "obsolete" in term.name:
            continue 
        
        writer.add_document(envo_id=term.id, name=term.name)
        term_count +=1

    writer.commit()

    print "Index creation completed. Processed %s terms from ontology" % term_count


if __name__ == "__main__":
    main(parse_cli_arguments())
