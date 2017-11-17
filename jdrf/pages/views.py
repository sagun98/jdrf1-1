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
    # set up logging config
    logging.basicConfig(filename='upload_file.log',level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s: %(message)s',
        datefmt='%m/%d/%Y %I:%M:%S %p')

    if request.method == 'POST':
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            # save the file as chunks
            file = request.FILES['file']
            logging.info("Uploading file: %s", file.name)
            user = str(request.user)
            logging.info("Uploading for user: %s", user)
            upload_folder = os.path.join(settings.UPLOAD_FOLDER,user)
            # if a folder does not exist for the user, then create
            if not os.path.isdir(upload_folder):
                try:
                    os.makedirs(upload_folder)
                except EnvironmentError:
                    logging.info("Unable to create upload folder")
                    raise

            upload_file = os.path.join(upload_folder,file.name)
            logging.info("Starting to upload file in chunks: %s", upload_file)
            with open(upload_file, 'wb+') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)
            logging.info("Finished uploading file")
    else:
        form = UploadForm()

    return render(request,'upload.html', {'form': form})

