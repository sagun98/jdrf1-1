
import sys
import os
import threading
import logging

def get_recursive_files_nonempty(folder,include_path=False):
    """ Get all files in all folder and subfolders that are not empty"""

    nonempty_files=[]
    for path, dirs, items in os.walk(folder):
        for file in items:
            file = os.path.join(path,file)
            if os.path.isfile(file) and os.stat(file).st_size > 0:
                if not include_path:
                    # remove the full path from the file name
                    file = os.path.basename(file)
                nonempty_files.append(file)
    return nonempty_files

def get_metadata_column_by_name(metadata_file, column_name):
    """ Read the metadata file and get a list of all of the data for the column """

    file_names=[]
    with open(metadata_file) as file_handle:
        # read in the header
        header = file_handle.readline().rstrip().split("\t")
        # file the column with the file names
        index = filter(lambda x: column_name in x[1].lower(), enumerate(header))[0][0]
        for line in file_handle:
            data=line.rstrip().split("\t")
            try:
                file_names.append(data[index])
            except IndexError:
                pass
    return file_names

def get_metadata_file_md5sums(metadata_file):
    """ Return the md5sums for all of the files """

    return zip(get_metadata_column_by_name(metadata_file, "file"),get_metadata_column_by_name(metadata_file, "md5sum"))

def get_metadata_file_names(metadata_file):
    """ Read the metadata file and get a list of all file names """
    return get_metadata_column_by_name(metadata_file, "file")

def check_metadata_files_complete(folder,metadata_file):
    """ Read the metadata and find all raw files for user.
        Then check that all files have metadata.
        Finally check that all files in the metadata exist. 
    """

    # get all of the files that have been uploaded
    all_raw_files = set(get_recursive_files_nonempty(folder))

    # remove the metadata file from the set of raw files
    raw_files = all_raw_files.difference([os.path.basename(metadata_file)])

    # check if there are not any raw files
    if len(list(raw_files)) == 0:
        return 1, "ERROR: Unable to find any uploaded raw files. Please upload files."

    # get the file names from the metadata
    try:
        metadata_files = set(get_metadata_file_names(metadata_file))
    except IndexError:
        return 1, "ERROR: Unable to find files in metadata file. Please update metadata."
    except EnvironmentError:
        return 1, "ERROR: Unable to find metadata file. Please upload metadata file."

    # check if there are not any files in the metadata
    if len(list(metadata_files)) == 0:
        return 1, "ERROR: Unable to find any file names in the metadata. Please update metadata."

    missing_from_metadata=raw_files.difference(metadata_files)
    missing_from_raw=metadata_files.difference(raw_files)

    message=""
    if missing_from_metadata:
        message="ERROR: The following raw files do not have metadata. Please update the metadata. Files: "+",".join(list(missing_from_metadata))
    if missing_from_raw:
        if message:
            message+=" "
        message+="ERROR: The following files in the metadata have not been uploaded. Please upload these files: "+",".join(list(missing_from_raw))

    error_code = 1
    if not message:
        message="SUCCESS! The metadata and raw files match! Please select the button to process the data."
        error_code = 0

    # return the error code and message
    return error_code, message

def verify_checksum(task):
    """ Verify the checksum matches that found in the metadata file """

    # read in the md5sums from the metadata file
    file_basename = os.path.basename(task.depends[0].name).replace(".md5sum","")
    try:
        md5sum = filter(lambda x: file_basename == x[0], get_metadata_file_md5sums(task.depends[1].name))[0][1]
    except IndexError:
        sys.stderr.write("ERROR: md5sum not found for sample: "+file_basename)
        sys.stderr.write(get_metadata_file_md5sums(task.depends[1].name))

    # read in the md5sum computed on the raw file
    with open(task.depends[0].name) as file_handle:
        new_sum = file_handle.readline().strip().split(" ")[0]

    if new_sum == md5sum:
        file_handle=open(task.targets[0].name,"w")
        file_handle.write("Match")
        file_handle.close()
    else:
        sys.stderr.write("ERROR: Sums do not match")
        sys.stderr.write(new_sum)
        sys.stderr.write(md5sum)

def create_folder(folder):
    """ Create a folder if it does not exist """

    # create the user process folder if it does not already exist
    if not os.path.isdir(folder):
        try:
            os.makedirs(folder)
        except EnvironmentError:
            logger.info("Unable to create folder: " + folder)
            raise

def check_metadata_files_md5sum(upload_folder,process_folder,metadata_file):
    """ Read the metadata to get the md5sums for all files.
        Check all files match the md5sums provided.
    """

    # get all of the files that have been uploaded
    all_raw_files = set(get_recursive_files_nonempty(upload_folder,include_path=True))

    # remove the metadata file from the set of raw files
    raw_files = list(all_raw_files.difference([metadata_file]))

    # create the user process folder if it does not already exist
    create_folder(process_folder)

    # create a workflow to check the md5sums for each file
    from anadama2 import Workflow

    # create a workflow without a command line interface (will not prompt)
    # and set output default to the process folder (to write the database)
    workflow = Workflow(cli=False)
    workflow.vars._arguments["output"].keywords["default"]= process_folder

    # create a workflow subfolder for the md5sum check files
    md5sum_folder = os.path.join(process_folder,"md5sum")
    create_folder(md5sum_folder)

    # for each raw input file, generate an md5sum file
    md5sum_outputs = [os.path.join(md5sum_folder,os.path.basename(file))+".md5sum" for file in raw_files]
    workflow.add_task_group(
        "md5sum [depends[0]] > [targets[0]]",
        depends=raw_files,
        targets=md5sum_outputs)

    # for each file, verify the checksum
    md5sum_checks = [os.path.join(md5sum_folder,os.path.basename(file))+".check" for file in raw_files]
    for sum_file, check_file in zip(md5sum_outputs, md5sum_checks):
        workflow.add_task(
            verify_checksum,
            depends=[sum_file,metadata_file],
            targets=[check_file])

    return raw_files, workflow

def check_md5sum_and_process_data(upload_folder,process_folder,metadata_file):
    """ First check md5sums then run the data through the workflow """

    raw_files, workflow = check_metadata_files_md5sum(upload_folder,process_folder,metadata_file)

    # check if there are raw files to process
    if len(list(raw_files)) == 0:
        return 1, "ERROR: Unable to find any uploaded raw files. Please upload files."

    results = process_data(workflow, raw_files, process_folder)

    return results

def process_data(workflow, input_files, process_folder):
    """ Run the files through the biobakery workflow """
    
    from biobakery_workflows.tasks import shotgun
    from biobakery_workflows import utilities, config

    # create anadama2 logger to avoid overlap with jdrf logger
    from anadama2.reporters import LoggerReporter
    log_file=os.path.join(process_folder, "anadama.log")
    logger_reporter = LoggerReporter(loglevel_str="INFO",log=log_file)
    handler = logging.FileHandler(log_file)
    logger_reporter.logger = logging.getLogger("anadama2")
    logger_reporter.logger.setLevel("INFO")
    logger_reporter.logger.addHandler(handler)

    # set the defaults
    threads = 1
    pair_identifier = ".R1"
    qc_options = ""
    remove_intermediate_output = True

    # get the contaminate databases for qc
    workflow_config = config.ShotGun()
    contaminate_databases = [workflow_config.kneaddata_db_human_genome,workflow_config.kneaddata_db_rrna]

    # determine the input extension for the files
    input_extension = input_files[0].split(".")[-1]

    # add qc tasks
    qc_output_files, filtered_read_counts = shotgun.quality_control(workflow, 
        input_files, input_extension, process_folder, threads, contaminate_databases, 
        pair_identifier, qc_options, remove_intermediate_output)
    input_extension = input_extension.replace(".gz","")

    # run taxonomic profiling
    merged_taxonomic_profile, taxonomy_tsv_files, taxonomy_sam_files = shotgun.taxonomic_profile(workflow, 
        qc_output_files,process_folder,threads,input_extension)

    # run functional profiling
    genes_relab, ecs_relab, path_relab, genes, ecs, path = shotgun.functional_profile(workflow,
        qc_output_files,input_extension,process_folder,threads,taxonomy_tsv_files,remove_intermediate_output)

    # run the workflow
    try:
        thread = threading.Thread(target=workflow.go, kwargs={'reporter':logger_reporter})
        thread.daemon = True
        thread.start()
    except threading.ThreadError:
        return 1, "ERROR: Unable to run workflow"

    return 0, "Success! The workflow is running. It will take at least a few hours. Look for an email notification when it has completed."

