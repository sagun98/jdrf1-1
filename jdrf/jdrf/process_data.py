
import sys
import os
import threading
import logging
import subprocess

import pandas as pd

from jdrf.metadata_schema import schema


# name the general workflow stdout/stderr files
WORKFLOW_STDOUT = "workflow.stdout"
WORKFLOW_STDERR = "workflow.stderr"

# name the files for the process subfolders
WORKFLOW_MD5SUM_FOLDER="md5sum_check"
WORKFLOW_DATA_PRODUCTS_FOLDER="data_products"
WORFLOW_VISUALIZATIONS_FOLDER="visualizations"


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


def errors_to_json(errors, metadata_df):
    """ Takes any JDRF metadata validation errors and converts them into a
        JSON object for consumption on the JDRF MIBC website via jquery 
        DataTables.
    """
    def _map_errors_to_df(err):
        """ Quick little closure to handle mapping our errors to the dataframe """
        metadata_df.loc[err.row, err.column] = "ERROR;%s;%s" % (err.value, err.message)
 
    map(_map_errors_to_df, errors)
    return metadata_df.to_json(orient='records')


def errors_to_csv(errors, metadata_df):
    """ Takes any JDRF metadata validation errors and writes them out to an 
        Excel file with cells containing errors denoted.
    """    
    pass


def validate_metadata_file(metadata_file, logger):
    """ Validates the provided JDRF metadata file and returns any errors 
        if they are present.
    """
    is_valid = False
    error_context = {}

    metadata_df = pd.read_csv(metadata_file, keep_default_na=False)
    errors = schema.validate(metadata_df)

    if errors:
        error_context['errors_datatable'] = errors_to_json(errors, metadata_df)
        error_context['errors_file'] = errors_to_csv(errors, metadata_df)

    return (is_valid, error_context)


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
        message="VERIFIED: All raw files have metadata.\n"
        message+="VERIFIED: All files in the metadata have been uploaded.\n"
        message+="SUCCESS! The metadata and raw files match.\n"
        message+="NEXT STEP: The files are now ready to be processed.\n"
        error_code = 0

    # return the error code and message
    return error_code, message

def create_folder(folder):
    """ Create a folder if it does not exist """
    # get the logger instance
    logger=logging.getLogger('jdrf1')

    # create the user process folder if it does not already exist
    if not os.path.isdir(folder):
        try:
            os.makedirs(folder)
        except EnvironmentError:
            logger.info("Unable to create folder: " + folder)
            raise

def subprocess_capture_stdout_stderr(command,output_folder):
    """ Run the command and capture stdout and stderr to files """

    stdout_file = os.path.join(output_folder, WORKFLOW_STDOUT)
    stderr_file = os.path.join(output_folder, WORKFLOW_STDERR)

    try:
        with open(stdout_file,"w") as stdout:
            with open(stderr_file,"w") as stderr:
                subprocess.check_call(command,stderr=stderr,stdout=stdout)
    except EnvironmentError, subprocess.CalledProcessError:
        raise

def run_workflow(upload_folder,process_folder,metadata_file):
    """ First run the md5sum steps then run the remainder of the workflow """

    # get the location of the workflow file
    folder = os.path.dirname(os.path.realpath(__file__))

    # get the workflow subfolders
    md5sum_check = os.path.join(process_folder,WORKFLOW_MD5SUM_FOLDER)
    data_products = os.path.join(process_folder,WORKFLOW_DATA_PRODUCTS_FOLDER)
    visualizations = os.path.join(process_folder,WORFLOW_VISUALIZATIONS_FOLDER)
 
    create_folder(md5sum_check)
    create_folder(data_products)
    create_folder(visualizations) 

    # get the input file extensions
    # get all of the files that have been uploaded
    all_raw_files = set(get_recursive_files_nonempty(upload_folder,include_path=True))

    # remove the metadata file from the set of raw files
    input_files = list(all_raw_files.difference([metadata_file]))

    if input_files[0].endswith(".gz"):
        extension = ".".join(input_files[0].split(".")[-2:])
    else:
        extension = input_files[0].split(".")[-1]

    # run the checksums
    subprocess_capture_stdout_stderr(["python",os.path.join(folder,"md5sum_workflow.py"),
        "--input",upload_folder,"--output",md5sum_check,"--input-metadata",
        metadata_file,"--input-extension",extension],md5sum_check)

    # run the wmgx workflow
    subprocess_capture_stdout_stderr(["biobakery_workflows","wmgx","--input",
        upload_folder,"--output",data_products,"--input-extension",
        extension,"--remove-intermediate-output","--bypass-strain-profiling"],data_products)

    # run the vis workflow
    subprocess_capture_stdout_stderr(["biobakery_workflows","wmgx_vis",
        "--input",data_products,"--output",visualizations,"--project-name",
        "JDRF MIBC Generated"],visualizations)

def check_workflow_running(user, process_folder):
    """ Check if any of the process workflows are running for a user """

    # get the logger instance
    logger=logging.getLogger('jdrf1')

    try:
        ps_output = subprocess.check_output(["ps","aux"])
    except EnvironmentError:
        ps_output = ""

    logger.info("Checking if workflow is running for user: " + user)
    user_workflow_processes = list(filter(lambda x: process_folder in x and "workflow" in x, ps_output))
    
    if user_workflow_processes:
        logger.info("Workflows running for user: ", "\n".join(user_workflow_processes))
        return True
    else:
        logger.info("No workflows running for user")
        return False

def check_md5sum_and_process_data(upload_folder,process_folder,metadata_file):
    """ Run the files through the md5sum check, biobakery workflow (data and vis) """
    
    # run the workflows
    try:
        thread = threading.Thread(target=run_workflow, args=[upload_folder,process_folder,metadata_file])
        thread.daemon = True
        thread.start()
    except threading.ThreadError:
        return 1, "ERROR: Unable to run workflow"
    
    return 0, "Success! The first workflow is running. It will take at least a few hours to run through all processing steps. The progress for each of the workflows will be shown below. Refresh this page to get the latest progress."

