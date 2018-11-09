
"""
Checks all datasets in the specified JDRF data folder to verify whether or 
not the dataset should be moved to interal release or flagged for public release.

In the case of a dataset not yet hitting either release status (or if ready for release)
the owner of the dataset will be notified how many days until internal release, public release 
or when either of these states is hit.
"""


import argparse
import glob
import os
import pwd
import sys

from collections import defaultdict
from itertools import groupby

import django
import ldap
import pendulum

# Setup up django outside of the environment 
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), os.pardir)))
os.environ['DJANGO_SETTINGS_MODULE'] = 'jdrf.settings'
django.setup()

from django.contrib.auth.models import User
from djang.conf import settings
from process_data import send_email_update

# Set default email options
EMAIL_FROM = "jdrfmibc-dev@hutlab-jdrf01.rc.fas.harvard.edu"
EMAIL_TO = "jdrfmibc-dev@googlegroups.com"

EMAIL_SERVER = "rcsmtp.rc.fas.harvard.edu"

jdrf_users = User.objects.all()


def get_all_archived_data_sets(archive_folder):
    """ Retrieve all archived folders and return a list of dictionaries 
    containing path to folder, owner email, study_name and date archived.
    """
    archived_datasets = {}
    study_sort = lambda d: os.path.basename(d).split('_')[0]

    data_dirs = list(filter(lambda d: os.path.isdir(d), glob.glob("%s/*/*" % archive_folder)))
    data_dirs = list(filter(lambda d: "public" not in d, data_dirs))
    data_dirs = sorted(data_dirs, key=study_sort)

    for (study_name, data_dirs) in groupby(data_dirs, lambda d: study_sort):
        archived_dirs = list(data_dirs)

        # Grab the users email
        stat_info = os.stat(archived_dirs[0])
        user = pwd.getpwuid(stat_info.st_uid)[0]
        user_email = jdrf_users.filter(username=user).get().email

        # Now get the date that this data was archived
        archive_date = os.path.basename(data_dir).rsplit("_", 1)[0].replace("%s_" % study_name, "")
        current_dt = pendulum.now()
        archive_dt = pendulum.from_format(archive_date, 'MM_D_YYYY')

        archived_datasets.defaultdict(list)
        archived_datasets[user].append({'study': study_name, 
                                        'dirs': archived_dirs, 
                                        'user_email': user_email, 
                                        'archive_date': archive_dt})

    return archived_datasets


def check_datasets_release_status(datasets, public_release, internal_release):
    """ Checks whether or not the passed in datasets meet any of the release 
    criteria specified. Release criteria should be passed in as months milestones 
    that must be hit before a dataset is released.
    """
    datasets_status = defaultdict(dict).defaultdict(list)
    current_dt = pendulum.now()

    for (username, datasets) in datasets.iteritems():
        for dataset in datasets:
            user_email = dataset.get('user_email')
            dataset_dirs = dataset.get('dirs')
            archive_dt= dataset.get('archive_date')

            public_release_dt = archive_dt.add(months=public_release)
            interal_release_dt = archive_dt.get('archive_date').add(months=internal_release)

            if current_dt >= public_release_dt and "public" not in dataset_dirs[0]:
                datasets_status[user_email]['public'].append((study, dirs))
            elif current_dt >= internal_release_dt and "internal" not in dataset_dirs[0]:
                datasets_status[user_email]['internal'].append((study, dirs))

                days_to_public = (public_release_dt - current_dt).days
                datasets_status[user_email]['pending'].append([study, dirs, {'public': days_to_public}])
            else:
                days_to_public = (public_release_dt - current_dt).days
                days_to_internal = (interal_release_dt - current_dt).days
                dataset_status[user_email]['pending'].append([study, dirs, {'public': days_to_public,
                                                                            'internal': days_to_internal}])                

    return datasets_status


def send_dataset_notifications(dataset_status, email_day):
    """Iterates over the collection of datasets and their release status and 
    send out emails for any datasets that have hit public or internal milestones 
    and for remaining datasets will send a status update if the current day matches
    the specified day to send email report out.
    """

    public_release_msg = ("Hello!\n\nThis is an automated message "
                          "to inform you that any data associated with the "
                          "study %s is set to be made public.\n\n"
                          "Please feel free to email the JDRF MIBC staff "
                          "if you have any questions regarding the data release "
                          "policy.\n\nThank you!\nThe JDRF MIBC team")

    internal_release_msg = ("Hello!\n\n This is an automated message "
                            "to inform you that any data associated with the "
                            "study %s is set to be made public.\n\n"
                            "Please feel free to email the JDRF MIBC staff "
                            "if you have any questions regarding the data release "
                            "policy.\n\nThank you!\nThe JDRF MIBC team")

    pending_release_msg = ("Hello!\n\nThis is an automated message "
                           "to inform you that data associated with the study "
                           "%s is set to be made public in %s days.")                            

    for (email, release_bins) in dataset_status.iteritems():
        public_datasets = release_bins.get('public')






archived_datasets = get_all_archived_data_sets(settings.ARCHIVE_FOLDER)

# With all our datasets we want to bucket them into three bins by user: 
#
#       1.) Datasets that haven't hit internal or public release time limit
#       2.) Datasets that hit internal but not public release time limit
#       3.) Datasets that have hit public release time limit
dataset_status = check_release_status(archived_datasets, settings.RELEASE_PUBLIC_MONTHS, 
                                      settings.RELEASE_INTERNAL_MONTHS)

send_dataset_notifications(dataset_status, settings.RELEASE_EMAIL_DAY)