
import os

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


def get_metadata_file_names(metadata_file):
    """ Read the metadata file and get a list of all file names """

    file_names=[]
    with open(metadata_file) as file_handle:
        # read in the header
        header = file_handle.readline().rstrip().split("\t")
        # file the column with the file names
        index = filter(lambda x: "file" in x[1].lower(), enumerate(header))[0][0]
        for line in file_handle:
            data=line.rstrip().split("\t")
            try:
                file_names.append(data[index])
            except IndexError:
                pass
    return file_names

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


