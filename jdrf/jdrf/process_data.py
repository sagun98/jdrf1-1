
import sys
import os
import threading
import logging
import subprocess
import time
import re

import smtplib
import socket
from email.mime.text import MIMEText

from django.conf import settings

# Set default email options
EMAIL_FROM = "jdrfmibc-dev@hutlab-jdrf01.rc.fas.harvard.edu"
EMAIL_TO = "jdrfmibc-dev@googlegroups.com"
EMAIL_SERVER = "rcsmtp.rc.fas.harvard.edu"

# Set default workflow config options
WMGX_PROCESSES="6"
WMGX_THREADS="8"
SixteenS_PROCESSES="1"
SixteenS_THREADS="30"

import pandas as pd

from jdrf.metadata_schema import schemas


# name the general workflow stdout/stderr files
WORKFLOW_STDOUT = "workflow.stdout"
WORKFLOW_STDERR = "workflow.stderr"

# name the files for the process subfolders
METADATA_FOLDER="metadata"
WORKFLOW_MD5SUM_FOLDER="md5sum_check"
WORKFLOW_DATA_PRODUCTS_FOLDER="data_products"
WORFLOW_VISUALIZATIONS_FOLDER="visualizations"


def get_recursive_files_nonempty(folder,include_path=False,recursive=True):
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
        if not recursive:
            break
    return nonempty_files

def get_metadata_column_by_name(metadata_file, column_name):
    """ Read the metadata file and get a list of all of the data for the column """

    file_names=[]
    with open(metadata_file) as file_handle:
        # read in the header
        header = file_handle.readline().rstrip().split(",")
        # file the column with the file names
        index = filter(lambda x: column_name in x[1].lower(), enumerate(header))[0][0]
        for line in file_handle:
            data=line.rstrip().split(",")
            try:
                file_names.append(data[index])
            except IndexError:
                pass
    return file_names

def get_metadata_file_md5sums(metadata_file):
    """ Return the md5sums for all of the files """

    return zip(get_metadata_column_by_name(metadata_file, "filename"),get_metadata_column_by_name(metadata_file, "md5_checksum"))

def get_metadata_file_names(metadata_file):
    """ Read the metadata file and get a list of all file names """
    return get_metadata_column_by_name(metadata_file, "file")


def delete_validation_files(upload_folder, logger):
    """Upon succesfully uploading a sample metadata file gets rid of any
    validation files if they exist.
    """
    validation_file = os.path.join(upload_folder, settings.METADATA_VALIDATION_FILE_NAME)

    if os.path.exists(validation_file):
        os.remove(validation_file)


def errors_to_json(errors, metadata_df):
    """ Takes any JDRF metadata validation errors and converts them into a
        JSON object for consumption on the JDRF MIBC website via jquery 
        DataTables.
    """
    def _map_errors_to_df(err):
        """ Quick little closure to handle mapping our errors to the dataframe """
        metadata_df.loc[err.row, err.column] = "ERROR;%s;%s" % (err.value, err.message)

    map(_map_errors_to_df, errors)
    return (metadata_df, metadata_df.to_json(orient='records'))


def errors_to_excel(metadata_df, output_folder):
    """ Takes any JDRF metadata validation errors and writes them out to an 
        Excel file with cells containing errors denoted.
    """    
    def _highlight_error(s):
        return ['background-color: red' if isinstance(v, str) 
                 and v.startswith('ERROR') else '' for v in s]
    def _color_error(s):
        return ['color: white' if isinstance(v, str)
                and v.startswith('ERROR') else 'black' for v in s]                 

    errors_file = os.path.join(output_folder, settings.METADATA_VALIDATION_FILE_NAME)
    styled_df = metadata_df.style.apply(_highlight_error).apply(_color_error)
    styled_df.to_excel(errors_file, index=False, engine='openpyxl')

    return errors_file
    

def validate_study_metadata(metadata_dict, logger):
    """ Validates the provded JDRF study metadata form and returns any errors
        present.
    """
    metadata_df = pd.DataFrame(metadata_dict)
    (is_valid, error_context) = _validate_metadata(metadata_df, 'study', logger)
    return (is_valid, metadata_df, error_context)


def validate_sample_metadata(metadata_file, output_folder, logger):
    """ Validates the provided JDRF sample metadata file and returns any errors
        presesnt.
    """
    is_valid = False
    error_context = {}
    metadata_df = None

    try:
       metadata_df = pd.read_csv(metadata_file, keep_default_na=False)
       (is_valid, error_context) = _validate_metadata(metadata_df, 'sample', logger, output_folder)
    except pd.errors.ParserError as pe:
        if "Error tokenizing data" in pe.message:
            line_elts = pe.message.split()
            line_number = int(line_elts[-3].replace(',', '')) - 1
            expected_fields = line_elts[-1]
            observed_fields = line_elts[-7]

            error_context['error_msg'] = "Line %s contained %s columns, expected %s columns" % (line_number, observed_fields, expected_fields)
        else:
            raise
    except:
        # If we have an error here we don't want to leave the user hanging
        error_context['error_msg'] = ("An unexpected error occurred. This error has been logged;" 
                                      "please contant JDRF support for help with your metadata upload")

    return (is_valid, metadata_df, error_context)


def _get_mismatched_columns(metadata_df, schema):
    """Compares the list of columns supplied in the metadata spreadsheet with the list 
    of valid columns in the corresponding metadata schema.
    """
    valid_columns = set([c.name for c in schema.columns])
    metadata_columns = set(metadata_df.columns.tolist())

    return list(valid_columns.symmetric_difference(metadata_columns))


def _validate_metadata(metadata_df, file_type, logger, output_folder=None):
    """ Validates the provided JDRF metadata DataFrame and returns any errors 
        if they are present.
    """
    error_context = {}

    schema = schemas[file_type]
    errors = schema.validate(metadata_df)
    
    is_valid = False if errors else True
    if errors:
        if len(errors) == 1:
            error_context['error_msg'] = str(errors[0])

            ## Adding a check here if we have a mismatch in the number of columns
            ## in the supplied metadata we will want to list which columns mismatch
            if "Invalid number of columns" in str(errors[0]):
                error_context['mismatch_cols'] = _get_mismatched_columns(metadata_df, schema)
        else:
            (errors_metadata_df, errors_json) = errors_to_json(errors,metadata_df)
            error_context['errors_datatable'] = errors_json

            if output_folder:
               error_context['errors_file'] = errors_to_excel(errors_metadata_df, output_folder)

    return (is_valid, error_context)


def check_metadata_files_complete(user,folder,metadata_file,study_file):
    """ Read the metadata and find all raw files for user.
        Then check that all files have metadata.
        Finally check that all files in the metadata exist. 
    """

    # get the study type
    study_type = get_study_type(study_file)

    # if study type is other, bypass verify
    if study_type == "other":
        message="BYPASS VERIFICATION: The study type is OTHER so verification is not required.\n"
        message+="NEXT STEP: The files are now ready to be processed.\n"
        error_code = 0

        # email status of verify
        subject="data verify run by user "+user
        send_email_update(subject,message)

        # return the error code and message
        return error_code, message


    # get all of the files that have been uploaded
    all_raw_files = set(get_recursive_files_nonempty(folder,recursive=False))

    # check if there are not any raw files
    if len(list(all_raw_files)) == 0:
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

    missing_from_metadata=all_raw_files.difference(metadata_files)
    missing_from_raw=metadata_files.difference(all_raw_files)

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

    # email status of verify
    subject="data verify run by user "+user
    send_email_update(subject,message)

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

def send_email_update(subject,message):
    """ Send an email to update the status of workflows """
    # get the logger instance
    logger=logging.getLogger('jdrf1')

    # create email message
    msg = MIMEText(message)
    msg['Subject'] = "JDRF1 MIBC Status Update: " + subject
    msg['From'] = EMAIL_FROM
    msg['To'] = EMAIL_TO

    logger.info("Sending email")
    logger.info("Email subject: " + subject)
    logger.info("Email message: " + message)

    # send the message
    try:
        s = smtplib.SMTP(EMAIL_SERVER,timeout=3)
        s.sendmail(msg['From'], msg['To'], msg.as_string())
        s.quit()
        logger.info("Email sent successfully")
    except (smtplib.SMTPRecipientsRefused, socket.gaierror, socket.timeout):
        logger.error("Unable to send email")

def subprocess_capture_stdout_stderr(command,output_folder):
    """ Run the command and capture stdout and stderr to files """
    # get the logger instance
    logger=logging.getLogger('jdrf1')

    stdout_file = os.path.join(output_folder, WORKFLOW_STDOUT)
    stderr_file = os.path.join(output_folder, WORKFLOW_STDERR)

    try:
        # use line buffering to write stdout/stderr
        with open(stdout_file,"wt",buffering=1) as stdout:
            with open(stderr_file,"wt",buffering=1) as stderr:
                subprocess.check_call(command,stderr=stderr,stdout=stdout)
    except (EnvironmentError, subprocess.CalledProcessError):
        logger.error("Unable to run subprocess command: " + " ".join(command))

    # check for error in stderr file
    time.sleep(2)
    try:
        with open(stderr_file) as file_handle:
            stderr_output = "".join(file_handle.readlines())
    except EnvironmentError:
        logger.error("Unable to read stderr file")
        stderr_output = ""

    if "ERROR" in stderr_output or "Failed" in stderr_output:
        logger.error("Error found in subprocess command stderr: " + " ".join(command))
        raise EnvironmentError

    logger.info("Subprocess command terminated")

def email_workflow_status(user,command,output_folder,workflow):
    """ Run the subprocess and send status emails """

    # start the subprocess
    subject="workflow "+workflow+" for user "+user
    message="The following subprocess was run to execute "+\
        "workflow "+workflow+" for user "+user+".\n\n"+" ".join(command)

    start_message = "Workflow started.\n\n"+message
    end_message = "Workflow finished without error.\n\n"+message
    error_message = "Workflow error.\n\n"+message+\
        "\n\nPlease review the workflow logs to determine the error."

    error = False
    try:
        send_email_update("Starting "+subject,start_message) 
        subprocess_capture_stdout_stderr(command,output_folder)
        send_email_update("Completed without error "+subject,end_message)
    except (EnvironmentError, subprocess.CalledProcessError):
        send_email_update("Ended with error "+subject,error_message)
        error = True

    return error

def get_study_type(study_file):
    """ Ready the metadata study file to determine the sequencing type """

    study_info="\n".join(open(study_file).readlines())
    if "16S" in study_info:
        return "16S"
    elif "other" in study_info:
        return "other"
    else:
        return "wmgx"

def get_study_name(study_file):
    """ Return the name of the study (alpha numeric only) """

    return re.sub(r'\W+','',open(study_file).readlines()[-1].split(",")[-1])

def run_workflow(user,upload_folder,process_folder,metadata_file,study_file):
    """ First run the md5sum steps then run the remainder of the workflow """

    # get the logger instance
    logger=logging.getLogger('jdrf1')

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
    all_raw_files = set(get_recursive_files_nonempty(upload_folder,include_path=True,recursive=False))

    # remove the metadata file from the set of raw files
    input_files = list(all_raw_files.difference([metadata_file]))

    if input_files[0].endswith(".gz"):
        extension = ".".join(input_files[0].split(".")[-2:])
    else:
        extension = input_files[0].split(".")[-1]

    # get the study type
    study_type = get_study_type(study_file)
    logger.info("Starting workflow for study type: " + study_type)

    # run the checksums
    command=["python",os.path.join(folder,"md5sum_workflow.py"),
        "--input",upload_folder,"--output",md5sum_check,"--input-metadata",
        metadata_file,"--input-extension",extension]
    error_state = False
    if study_type != "other":
        error_state = email_workflow_status(user,command,md5sum_check,"md5sum")

    # run the wmgx workflow
    if study_type == "16S":
        command=["biobakery_workflows","16s","--input",
            upload_folder,"--output",data_products,"--input-extension",
            extension,"--local-jobs",SixteenS_PROCESSES,"--threads",SixteenS_THREADS]
        if not error_state:
            error_state = email_workflow_status(user,command,data_products,"16s")

        # run the vis workflow
        command=["biobakery_workflows","16s_vis",
            "--input",data_products,"--output",visualizations,"--project-name",
            "JDRF MIBC Generated"]
        if not error_state:
            error_state = email_workflow_status(user,command,visualizations,"visualization")
    elif study_type != "other":
        command=["biobakery_workflows","wmgx","--input",
            upload_folder,"--output",data_products,"--input-extension",
            extension,"--remove-intermediate-output","--bypass-strain-profiling",
            "--local-jobs",WMGX_PROCESSES,"--threads",WMGX_THREADS]
        if not error_state:
            error_state = email_workflow_status(user,command,data_products,"wmgx")

        # run the vis workflow
        command=["biobakery_workflows","wmgx_vis",
            "--input",data_products,"--output",visualizations,"--project-name",
            "JDRF MIBC Generated"]
        if not error_state:
            error_state = email_workflow_status(user,command,visualizations,"visualization")

    # run the archive and transfer workflow
    archive_folder = os.path.join(settings.ARCHIVE_FOLDER,user)
    create_folder(archive_folder)
    study_name = get_study_name(study_file)
    command=["python",os.path.join(folder,"archive_workflow.py"),
        "--input-upload",upload_folder,"--input-processed",process_folder,
        "--key",settings.SSH_KEY,"--remote",settings.REMOTE_TRANSFER_SERVER,
        "--study",study_name,"--output",archive_folder,"--output-transfer",
        os.path.join(settings.REMOTE_TRANSFER_FOLDER,user)+"/"]
    if not error_state:
        email_workflow_status(user,command,archive_folder,"archive and transfer")

def check_workflow_running(user, process_folder):
    """ Check if any of the process workflows are running for a user """

    # get the logger instance
    logger=logging.getLogger('jdrf1')

    try:
        ps_output = subprocess.check_output(["ps","aux"]).split("\n")
    except EnvironmentError:
        ps_output = []

    logger.info("Checking if workflow is running for user: " + user)
    user_workflow_processes = list(filter(lambda x: process_folder in x and "workflow" in x, ps_output))
    
    if user_workflow_processes:
        logger.info("Workflows running for user: ", "\n".join(user_workflow_processes))
        return True
    else:
        logger.info("No workflows running for user")
        return False

def check_md5sum_and_process_data(user,upload_folder,process_folder,metadata_file,study_file):
    """ Run the files through the md5sum check, biobakery workflow (data and vis) """

    # run the workflows
    try:
        thread = threading.Thread(target=run_workflow, args=[user,upload_folder,process_folder,metadata_file,study_file])
        thread.daemon = True
        thread.start()
    except threading.ThreadError:
        return 1, "ERROR: Unable to run workflow"
    
    return 0, "Success! The first workflow is running. It will take at least a few hours to run through all processing steps. The progress for each of the workflows will be shown below. Refresh this page to get the latest progress."

