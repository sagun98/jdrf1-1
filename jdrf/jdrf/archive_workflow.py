
import os
import sys
import datetime

# create a workflow to check the md5sums for each file
from anadama2 import Workflow
from biobakery_workflows import utilities

# create a workflow and get the arguments
workflow = Workflow(remove_options=["input"])
workflow.add_argument("input-upload", desc="the folder of raw uploaded data", required=True)
workflow.add_argument("input-processed", desc="the folder of processed data", required=True)
workflow.add_argument("key", desc="the key file to use for the transfer", required=True)
workflow.add_argument("user", desc="the user id for the transfer", required=True)
workflow.add_argument("remote", desc="the remote host name for the transfer", required=True)
workflow.add_argument("study", desc="the name of the study", required=True)
workflow.add_argument("output-transfer", desc="the folder to transfer the data", required=True)
args = workflow.parse_args()

# archive the raw input files
date=datetime.datetime.now()
study_folder=args.study+"_"+str(date.month)+"_"+str(date.day)+"_"+str(date.year)
archive_folder = os.path.join(args.output,study_folder)

upload_archive = archive_folder+"_uploaded"
utilities.create_folders(upload_archive)

task1=workflow.add_task(
    "mv [args[0]]/* [args[1]]/",
    args=[args.input_upload,upload_archive])

# archive the processed files
process_archive = archive_folder+"_processed"
utilities.create_folders(process_archive)

task2=workflow.add_task(
    "mv [args[0]]/* [args[1]]/",
    depends=task1,
    args=[args.input_processed,process_archive])

task3=workflow.add_task(
    "cp [args[0]]/metadata/metadata*.tsv [args[1]]/",
    depends=task2,
    args=[upload_archive,process_archive])

# transfer the processed files to a named study folder on remote machine
task4=workflow.add_task(
    "rsync --exclude '*.fastq*' --exclude '*.fq*' --exclude '*.fasta*' --exclude '*.fa*' --exclude '*.bam' --exclude '*.sam' --exclude '*.vcf*' --recursive -e 'ssh -i [args[0]] -l [args[1]]' [args[2]] [args[3]]:[args[4]]",
    depends=task3,
    args=[args.key, args.user, process_archive, args.remote, args.output_transfer])

workflow.go()

