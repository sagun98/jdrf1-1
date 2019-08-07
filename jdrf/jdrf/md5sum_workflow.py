
import os
import sys

# create a workflow to check the md5sums for each file
from anadama2 import Workflow
from biobakery_workflows import utilities


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

def verify_checksum(task):
    """ Verify the checksum matches that found in the metadata file """

    # read in the md5sums from the metadata file
    original_input = os.path.basename(task.depends[0].name)
    try:
        md5sum = filter(lambda x: original_input == x[0], get_metadata_file_md5sums(task.depends[2].name))[0][1]
    except IndexError:
        error_msg = "ERROR: md5sum not found for sample: " + task.depends[0].name + "\n"
        sys.stderr.write(error_msg)
        sys.stderr.write("\n".join([file+":"+sum for file,sum in get_metadata_file_md5sums(task.depends[2].name)]) + "\n")
        raise Exception(error_msg)

    # read in the md5sum computed on the raw file
    with open(task.depends[1].name) as file_handle:
        new_sum = file_handle.readline().strip().split(" ")[0]

    if new_sum.lower() == md5sum.lower():
        file_handle=open(task.targets[0].name,"w")
        file_handle.write("Match")
        file_handle.close()
    else:
        error_msg="ERROR: Sums do not match for file {0}\nComputed Sum: {1}\nExpected Sum: {2}".format(task.depends[1].name,new_sum,md5sum)
        sys.stderr.write(error_msg)
        raise Exception(error_msg)

# create a workflow and get the arguments
workflow = Workflow()
workflow.add_argument("input-metadata", desc="the metadata file", required=True)
workflow.add_argument("input-extension", desc="the input file extension", required=True)
args = workflow.parse_args()

# get all of the input files
input_files = utilities.find_files(args.input, extension=args.input_extension, exit_if_not_found=True)
sample_names=utilities.sample_names(input_files,args.input_extension)

# for each raw input file, generate an md5sum file
md5sum_outputs = [os.path.join(args.output, output_file_name)+".md5sum" for output_file_name in sample_names]
workflow.add_task_group(
    "md5sum [depends[0]] > [targets[0]]",
    depends=input_files,
    targets=md5sum_outputs)

# for each file, verify the checksum
md5sum_checks = [os.path.join(args.output, check_file_name)+".check" for check_file_name in sample_names]
for in_file, sum_file, check_file in zip(input_files, md5sum_outputs, md5sum_checks):
    workflow.add_task(
        verify_checksum,
        depends=[in_file, sum_file, args.input_metadata],
        targets=[check_file])

workflow.go()
