# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import sys
import time

from django.conf import settings

from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.template import RequestContext
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.csrf import requires_csrf_token

from django.http import StreamingHttpResponse

from jdrf import process_data

from .forms import UploadForm

import logging

def get_user_and_folders_plus_logger(request):
    """ Get the user and all of the user folders """

    # get the default logger
    logger=logging.getLogger('jdrf1')

    # get the list of raw files to process
    user = str(request.user)
    logger.info("Current user: %s", user)
    # get the location of the upload file for the user
    upload_folder = os.path.join(settings.UPLOAD_FOLDER,user)
    logger.info("Upload folder: %s", upload_folder)
    # get the location of the process folder for the user
    process_folder = os.path.join(settings.PROCESS_FOLDER,user)
    logger.info("Process folder: %s", process_folder)

    return logger, user, upload_folder, process_folder


@login_required(login_url='/login/')
@csrf_exempt
@requires_csrf_token
def upload_files(request):
    # get the user, folders, and logger
    logger, user, upload_folder, process_folder = get_user_and_folders_plus_logger(request)
    if request.method == 'POST':
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            # save the file as chunks
            # use chunking from plupload (so request.FILES['file'] might be blob)
            # write to temp file then move when all chunks are written
            file = request.FILES['file']
            file_name = request.POST['name']
            file_name_part = file_name+".part"
            logger.info("Uploading file in chunks: %s", file_name_part)
            upload_folder = os.path.join(settings.UPLOAD_FOLDER,user)
            # if a folder does not exist for the user, then create
            if not os.path.isdir(upload_folder):
                try:
                    os.makedirs(upload_folder)
                except EnvironmentError:
                    logger.info("Unable to create upload folder")
                    raise

            upload_file = os.path.join(upload_folder,file_name_part)
            logger.info("Starting to upload file in chunks: %s", upload_file)
            with open(upload_file, 'a') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)

            logger.info("Finished uploading file chunk")

            # move the file if all chunks have been written
            chunks = int(request.POST['chunks'])
            chunk = int(request.POST['chunk'])
            if chunks == 0 or chunk == chunks -1:
                os.rename(upload_file, os.path.join(upload_folder,file_name))
                logger.info("Finished uploading file")
    else:
        form = UploadForm()

    return render(request,'upload.html', {'form': form})

def try_read_file(file_name):
    """ Try to read the file if it exists """

    lines=""
    try:
        with open(file_name) as file_handle:
            lines="".join(file_handle.readlines())
    except EnvironmentError:
        pass

    return lines

@login_required(login_url='/login/')
@csrf_exempt
@requires_csrf_token
def process_files(request):
    # get the user, folders, and logger
    logger, user, upload_folder, process_folder = get_user_and_folders_plus_logger(request)
 
    # set the default responses
    responses={"message1":[],"message2":[]}
 
    responses["raw_input"]="The following raw files have been uploaded and are ready to verify:\n"
    responses["raw_input"]+="\n".join(process_data.get_recursive_files_nonempty(upload_folder,include_path=False))+"\n"

    if request.method == 'POST':
        logger.info("Post from process page received")
        metadata_file = os.path.join(upload_folder,settings.METADATA_FILE_NAME)
        logger.info("Metadata file: %s", metadata_file)
        process_folder = os.path.join(settings.PROCESS_FOLDER,user)
        logger.info("Process folder: %s", process_folder)

        if "verify" in request.POST:
            # check the metadata matches the raw uploads
            responses["message1"] = process_data.check_metadata_files_complete(user,upload_folder,metadata_file)
        elif "process" in request.POST:
            responses["message2"] = process_data.check_md5sum_and_process_data(user,upload_folder,process_folder,metadata_file)

    # log messages
    for message_name, message in responses.items():
        if message and not message_name == "raw_input":
            logger.info("Error code: %s", message[0])
            logger.info("Message: %s", message[1])

    # check if the workflow is running
    responses["workflow_running"] = process_data.check_workflow_running(user, process_folder)

    # get the stdout for the processing workflows
    stdout_file=process_data.WORKFLOW_STDOUT
    responses["md5sum_stdout"]=try_read_file(os.path.join(process_folder,process_data.WORKFLOW_MD5SUM_FOLDER,stdout_file))
    responses["data_products_stdout"]=try_read_file(os.path.join(process_folder,process_data.WORKFLOW_DATA_PRODUCTS_FOLDER,stdout_file))
    responses["visualizations_stdout"]=try_read_file(os.path.join(process_folder,process_data.WORFLOW_VISUALIZATIONS_FOLDER,stdout_file))

    # if the workflow just started, wait for a refresh before updating status
    if not responses["message2"]:
        if not responses["workflow_running"]:
            if list(filter(lambda x: "fail" in x, [responses["md5sum_stdout"],responses["data_products_stdout"],responses["visualizations_stdout"]])):
                # one of the workflows had a task that failed
                responses["message2"]=(1, "ERROR: The workflows have finished running. One of the tasks failed.")
            elif len(list(filter(lambda x: "Finished" in x, [responses["md5sum_stdout"],responses["data_products_stdout"],responses["visualizations_stdout"]])))  == 3:
                responses["message2"]=(0, "Success! All three workflows (md5sum check, data processing, and visualization) finished without error.")
            elif ( responses["md5sum_stdout"] and not ( responses["data_products_stdout"] or responses["visualizations_stdout"] ) or 
                responses["md5sum_stdout"] and responses["data_products_stdout"] and not responses["visualizations_stdout"] ):
                # add the case where we are in between workflows running
                responses["message2"]=(0, "The processing workflows (md5sum check, data processing, and visualization) are still running.")
        elif responses["md5sum_stdout"] or responses["data_products_stdout"] or responses["visualizations_stdout"]:
            responses["message2"]=(0, "The processing workflows (md5sum check, data processing, and visualization) are still running.")

    return render(request,'process.html',responses)

def get_file_size(file):
    """ Get the size of the file """

    size = 0 
    try:
        size = os.stat(file).st_size
    except EnvironmentError:
        pass

    # change units based on total size
    units = " "
    for type in ["K","M","G"]:
        if size / 1024.0 > 1.0:
            size = size / 1024
            units = type

    return str(size)+" "+units


def get_mtime(file):
    """ Get the last time a file was modified as a date string """

    return time.ctime(os.path.getmtime(file))

@login_required(login_url='/login/')
def download_files(request):
    """ List all of the processed files available for the user to download """

    # get the user, folders, and logger
    logger, user, upload_folder, process_folder = get_user_and_folders_plus_logger(request)
    logger.info("Listing files for user: %s", user)

    # get all of the files in the user process folder, with directories
    list_files = []
    for path, directories, files in os.walk(process_folder):  
        # remove the base process folder form the path
        reduced_path = path.replace(process_folder,"")
        # remove path sep if first character
        if reduced_path.startswith(os.sep):
            reduced_path = reduced_path[1:]
        current_set = []
        for file in files:
            file_path = os.path.join(path,file)
            # check that this is a file with an extension
            if os.path.isfile(file_path) and "." in file:
                current_set.append((os.path.join(reduced_path,file), get_file_size(file_path), get_mtime(file_path)))
        # add the files sorted
        if current_set:
            list_files+=sorted(current_set, key=lambda x: x[0])

    # remove any of the anadama db files
    list_files = list(filter(lambda x: not ".anadama" in x[0], list_files))

    # organize the files into the three workflow folders
    response={}
    response["md5sum_files"] = [(file.replace(process_data.WORKFLOW_MD5SUM_FOLDER+os.sep,""), file, size, mtime) for file, size, mtime in list(filter(lambda x: x[0].startswith(process_data.WORKFLOW_MD5SUM_FOLDER), list_files))]
    response["data_product_files"] = [(file.replace(process_data.WORKFLOW_DATA_PRODUCTS_FOLDER+os.sep,""), file, size, mtime) for file, size, mtime in list(filter(lambda x: x[0].startswith(process_data.WORKFLOW_DATA_PRODUCTS_FOLDER), list_files))]
    response["visualization_files"] = [(file.replace(process_data.WORFLOW_VISUALIZATIONS_FOLDER+os.sep,""), file, size, mtime) for file, size, mtime in list(filter(lambda x: x[0].startswith(process_data.WORFLOW_VISUALIZATIONS_FOLDER), list_files))]

    return render(request,'download.html',response)

@login_required(login_url='/login/')
def download_file(request, file_name):
    """ Download the file from the user's processed files folder """
    # get the user, folders, and logger
    logger, user, upload_folder, process_folder = get_user_and_folders_plus_logger(request)
    logger.info("Downloading file for user: %s", user)

    # get file path
    download_file = os.path.join(process_folder,file_name)
    logger.info("File to download: %s", download_file)

    response = StreamingHttpResponse(open(download_file, 'r'), content_type="text")
    response['Content-Disposition'] = 'attachment; filename="'+os.path.basename(download_file)+'"'

    return response
