
import os
import sys
import datetime

# constants 
ARCHIVE_FOLDER = "/opt/archive_folder/"
COUNT_FILE = os.path.join(ARCHIVE_FOLDER,"data_deposition_counts.csv")
PUBLIC_COUNT_FILE = os.path.join(ARCHIVE_FOLDER,"data_deposition_counts_public.csv")

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
workflow.add_argument("count-script", desc="the script to update the data stats", required=True)
args = workflow.parse_args()

# archive the raw input files
date=datetime.datetime.now()
study_folder=args.study+"_"+str(date.month)+"_"+str(date.day)+"_"+str(date.year)
archive_folder = os.path.join(args.output,study_folder)

upload_archive = archive_folder+"_uploaded"
utilities.create_folders(upload_archive)

task1=workflow.add_task(
    "mv --backup [args[0]]/* [args[1]]/",
    args=[args.input_upload,upload_archive])

# archive the processed files
process_archive = archive_folder+"_processed"
utilities.create_folders(process_archive)

task2=workflow.add_task(
    "mv --backup [args[0]]/* [args[1]]/",
    depends=task1,
    args=[args.input_processed,process_archive])

task3=workflow.add_task(
    "cp [args[0]]/metadata/metadata*.tsv [args[1]]/",
    depends=task2,
    args=[upload_archive,process_archive])

task4=workflow.add_task(
    "rsync --ignore-existing [args[0]]/metadata/MANIFEST [args[1]] && rm [args[0]]/metadata/MANIFEST",
    depends=task3,
    args=[upload_archive, os.path.dirname(archive_folder)]
)

# transfer the processed files to a named study folder on remote machine
task5=workflow.add_task(
    "rsync --exclude '*.fastq*' --exclude '*.fq*' --exclude '*.fasta*' --exclude '*.fa*' --exclude '*.bam' --exclude '*.sam' --exclude '*.vcf*' --recursive -e 'ssh -i [args[0]] -l [args[1]]' [args[2]] [args[3]]:[args[4]]",
    depends=task4,
    args=[args.key, args.user, process_archive, args.remote, args.output_transfer])

# update the stats
task6=workflow.add_task(
    "python [args[0]] [targets[0]] [targets[1]]",
    depends=task5,
    targets=[COUNT_FILE, PUBLIC_COUNT_FILE],
    args=args.count_script)

# transfer the updated counts files
for filename in [COUNT_FILE, PUBLIC_COUNT_FILE]:
    workflow.add_task(
        "rsync -e 'ssh -i [args[0]] -l [args[1]]' '[depends[0]]' [args[2]]:[args[3]]",
        depends=[filename,task6],
        args=[args.key, args.user, args.remote, os.path.abspath(os.path.join(args.output_transfer,os.pardir))+"/"])

workflow.go()

