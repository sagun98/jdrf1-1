# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import sys

from django.conf import settings

from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.template import RequestContext
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.csrf import requires_csrf_token

from .forms import UploadForm

import logging

@login_required(login_url='/login/')
@csrf_exempt
@requires_csrf_token
def upload_files(request):
    # get the logger
    logger=logging.getLogger('jdrf1')
    if request.method == 'POST':
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            # save the file as chunks
            file = request.FILES['file']
            logger.info("Uploading file: %s", file.name)
            user = str(request.user)
            logger.info("Uploading for user: %s", user)
            upload_folder = os.path.join(settings.UPLOAD_FOLDER,user)
            # if a folder does not exist for the user, then create
            if not os.path.isdir(upload_folder):
                try:
                    os.makedirs(upload_folder)
                except EnvironmentError:
                    logger.info("Unable to create upload folder")
                    raise

            upload_file = os.path.join(upload_folder,file.name)
            logger.info("Starting to upload file in chunks: %s", upload_file)
            with open(upload_file, 'wb+') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)
            logger.info("Finished uploading file")
    else:
        form = UploadForm()

    return render(request,'upload.html', {'form': form})

@login_required(login_url='/login/')
@csrf_exempt
@requires_csrf_token
def process_files(request):
    # get the logger
    logger=logging.getLogger('jdrf1')

    responses={"message1":"","message2":""}
    if request.method == 'POST':
        logger.info("Post from process page received")
        if "verify" in request.POST:
            responses["message1"]="Verify post received"
        elif "process" in request.POST:
            responses["message2"]="Process post received"

    # log messages
    for message_name, message in responses.items():
        if message:
            logger.info(message)

    return render(request,'process.html',responses)
