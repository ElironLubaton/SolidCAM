import os
import sys

from Process_Jobs import process_non_drilling_jobs, process_drilling_jobs
from Utilities_and_Cosmetics import read_json


"""
This notebook's purpose is processing the JSON files of parts in order to assign jobs to their relevant recognized hole group in the relevant topology.  
This notebook is used under the assumption that the JSON file is valid, where validation can be checked in the notebook 'JSON Validation'.

The data is being processed as follows:  
1 - Iterating on the each part's jobs.

2 - Dividing the jobs to either drilling jobs or non-drilling jobs.  

3 - Creating a dictionary that holds all the topologies.

4 - Assigning holes groups to their topology.  

5 - Assigning jobs by the order they have been performed to their hole group.
"""



"""
The main loop goes over all the parts, and processes each part.
A part can be processed by either two functions:
  1. process_drilling_jobs: as its name suggests, it processes only drilling jobs -
     jobs that contain "drill" field in their JSON.
     *Note that if a job contains "drill" field, but 'recognized_holes_groups' field is missing,
     this job is probably a pre-drilling for a pocket.

  2. process_non_drilling_jobs: as its name suggests, it processes jobs that
     doesn't involve drilling.
     Such jobs ('Profile' for example) does NOT contain any hole information. They contain
     only the values of the holes they are working on - 'vals' field, under 'geometry' field.
"""


topologies_dict = {} # Holds all the different topologies

dir_path = 'C:/Users/eliron.lubaton/Desktop/SolidCAM/CodePy/JSON'

drilling_types = ["NC_DRILL_OLD", "NC_DRILL_DEEP", "NC_THREAD", "NC_DRILL_HR", "NC_JOB_MW_DRILL_5X"]

### Processing loop ###

# Going over on all the parts, and process them
for part_name in os.listdir(dir_path):
    # Processing only files that ends with .json
    if part_name.endswith('.json'):
        file_path = os.path.join(dir_path, part_name)

        # Read the JSON file
        data = read_json(file_path)

        # Checking if the data is in inch or mm
        is_inch = 1 if (data["event_data"]["part"]["is_inch"]==True) else 0

        # Going over all jobs in the part

        for job in data["event_data"]["jobs"]:
        # for job_number, job in enumerate(data["event_data"]["jobs"]):
          # # If the data is in inch, converting it to mm
          # if is_inch:
          #   job = convert_json_units(job)

          # True if the job is one of the drilling jobs
          if job["type"] in drilling_types:
            # Checking if the job is not pre-drilling for creating pockets
            if "recognized_holes_groups" in job['geometry']:
              process_drilling_jobs(job, job["job_number"], job["type"], part_name, topologies_dict)
          else:
            # The job is NOT a drilling job - for now, refers to Profile and Chamfer
            process_non_drilling_jobs(job, job["job_number"], topologies_dict)




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
    diameters += [group.diameter] * len(group.centers)
    depths += [group.hole_depth] * len(group.centers)
  print("______________________________________________________\n")
