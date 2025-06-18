import os

from Process_Jobs import process_jobs
from Utilities_and_Cosmetics import read_json, validate_job


"""
This notebook's purpose is processing the JSON files of parts in order to assign jobs to their relevant recognized hole group in the relevant topology.  
This notebook is used under the assumption that the JSON file is valid, where validation can be checked in the notebook 'JSON Validation'.

The data is being processed as follows:  
1 - Iterating on the each part's jobs.

2 - Creating a dictionary that holds all the topologies.

3 - Assigning holes groups to their topology.  

4 - Assigning jobs by the order they have been performed to their hole group.
"""


topologies_dict = {} # Holds all the different topologies masks

dir_path = 'C:/Users/eliron.lubaton/Desktop/SolidCAM/CodePy/JSONs'

drilling_types = ["NC_DRILL_OLD", "NC_DRILL_DEEP", "NC_THREAD", "NC_DRILL_HR", "NC_JOB_MW_DRILL_5X"]
non_drilling_types = ["NC_PROFILE", "NC_CHAMFER"]

### Processing loop ###

# def processing_loop():
#     """
#     This function goes over pair of files: JSON file and a corresponding EXCEL file (which contains
#     more information on the JSON file).
#     """
#     # Going over all subdirectories inside dir_path
#     for subdir_name in os.listdir(dir_path):
#         subdir_path = os.path.join(dir_path, subdir_name)
#
#         # Skip if not a directory
#         if not os.path.isdir(subdir_path):
#             continue
#
#         # Initialize file paths
#         json_file_path = None
#         excel_file_path = None
#
#         # Search for .json and .xls files inside the subdirectory
#         for file_name in os.listdir(subdir_path):
#             if file_name.endswith('.json'):
#                 json_file_path = os.path.join(subdir_path, file_name)
#             elif file_name.endswith('.xls') or file_name.endswith('.xlsx'):
#                 excel_file_path = os.path.join(subdir_path, file_name)
#
#         if json_file_path is None or excel_file_path is None:
#             print(f"Missing .json or .xls file in {subdir_name}")
#             continue
#
#         # Read and process the JSON file
#         data = read_json(json_file_path)
#
#         # Checking if the data is in inch or mm
#         is_inch = 1 if (data["event_data"]["part"]["is_inch"] == True) else 0
#
#         # Processing the JSON file - Going over all jobs in the part
#         print(f"Processing part: {subdir_name}")
#         for job in data["event_data"]["jobs"]:
#             # # If the data is in inch, converting it to mm
#             # if is_inch:
#             #   job = convert_json_units(job)
#
#             # Making sure all the relevant fields in the JSON exist and are correct
#             validate_job(job, json_file_path)
#
#             # Checking if the job is not pre-drilling for creating pockets
#             if job["geometry"].get("recognized_holes_groups") is not None:
#                 # Processing the job
#                 process_jobs(job, json_file_path, topologies_dict)
#
#
#         # Processing the EXCEL file
#         process_excel_files(excel_file_path)
#
#         print(f"\n***********************\n")

def process_excel_files(file_path):
    return


def processing_loop():
    # Going over on all the parts, and process them
    for part_name in os.listdir(dir_path):
        # Processing only files that ends with .json
        if part_name.endswith('.json'):
            file_path = os.path.join(dir_path, part_name)

            # Read the JSON file
            data = read_json(file_path)

            # Going over all jobs in the part
            print(f"part name is: {part_name}")
            for job in data["event_data"]["jobs"]:
                # Processing only specific jobs
                if job["type"] not in drilling_types and job["type"] not in non_drilling_types:
                    continue

                # # Making sure all the relevant fields in the JSON exist and are correct
                # validate_job(job, part_name)

                # Checking if the job is not pre-drilling for creating pockets
                if job["geometry"].get("recognized_holes_groups") is not None:
                # if "recognized_holes_groups" in job['geometry']:
                    # Processing the job
                    process_jobs(job, part_name, topologies_dict)
            print(f"\n***********************\n")






processing_loop()






          # # True if the job is one of the drilling jobs
          # if job["type"] in drilling_types:
          #   validate_job(job) # sending True because it's a drilling job
          #   # Checking if the job is not pre-drilling for creating pockets
          #   if "recognized_holes_groups" in job['geometry']:
          #     process_drilling_jobs(job, part_name, topologies_dict)
          #
          # else:
          #   # The job is NOT a drilling job - for now, refers to Profile and Chamfer
          #   validate_job(job) # sending False because it's NOT a drilling job
          #   process_non_drilling_jobs(job, topologies_dict)




### Printing Stats
"""
Most of the stats that are printed here are used for DEBUGGING purposes.
In order to change the stats that are being printed, head to the method 'print' under
'HoleGroup' class.
"""

bold_s = '\033[1m' # Start to write in bold
bold_e = '\033[0m' # End to write in bold

# For each topology, updates the dictionary that holds all the jobs orders of all holes groups
# It is used only for statistics purposes
for _, topology in topologies_dict.items():
  topology.update_jobs_orders_dict()

diameters = []
depths = []


# # Printing the updated dictionary, and saving the output
# with open("HoleWizard.PRT.ML.txt", "w") as file:
#     sys.stdout = file
#     # Print the updated holes_dict
#     for _ , topology in topologies_dict.items():
#       print(f"{bold_s}Topology: {topology.topology}{bold_e}")
#       print(f"Total number of hole groups: {len(topology.holes_groups)}")
#       total_instances = 0
#       for hole_group in topology.holes_groups:
#         total_instances += len(hole_group.centers)
#       print(f"Total number of instances: {total_instances}\n")
#
#
#       for group in topology.holes_groups:
#         group.print()
#         diameters += [group.diameter] * len(group.centers)
#         depths += [group.hole_depth] * len(group.centers)
#       print("______________________________________________________\n")
#     sys.stdout = sys.__stdout__  # Reset stdout back to normal



# Printing the updated dictionary, and saving the output
for _ , topology in topologies_dict.items():
  print(f"{bold_s}Topology: {topology.topology}{bold_e}")
  print(f"Total number of hole groups: {len(topology.holes_groups)}")
  total_instances = 0
  for hole_group in topology.holes_groups:
    total_instances += len(hole_group.centers)
  print(f"Total number of instances: {total_instances}\n")


  for group in topology.holes_groups:
    group.print()
  print("______________________________________________________\n")
