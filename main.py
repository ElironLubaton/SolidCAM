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
non_drilling_types = ["NC_PROFILE", "NC_CHAMFER", "NC_JOB_HSS_PARALLEL_TO_CURVE"]

### Processing loop ###


def processing_loop():
    # Going over on all the parts, and process them
    for part_name in os.listdir(dir_path):
        # Processing only files that ends with .json
        if part_name.endswith('.json'):
            file_path = os.path.join(dir_path, part_name)

            # Read the JSON file
            data = read_json(file_path)

            # Going over all jobs in the part
            print(f"Part name is: {part_name}")
            for job in data["event_data"]["jobs"]:
                # Processing only specific jobs
                if job["type"] not in drilling_types and job["type"] not in non_drilling_types:
                    continue

                # Making sure all the relevant fields in the JSON exist and are correct
                validate_job(job, part_name)

                # Checking if the job is not pre-drilling for creating pockets
                if job["geometry"].get("recognized_holes_groups") is not None:
                    # Processing the job
                    process_jobs(job, part_name, topologies_dict)
            print(f"\n***********************\n")

processing_loop()





### Printing Stats
"""
Most of the stats that are printed here are used for DEBUGGING purposes.
In order to change the stats that are being printed, head to the method 'print' under
'HoleGroup' class.
"""

bold_s = '\033[1m' # Start to write in bold
bold_e = '\033[0m' # End to write in bold

# Printing the updated dictionary, and saving the output
for topology in topologies_dict.values():
  print(f"{bold_s}Topology: {topology.topology} | Mask: {topology.topology_mask}{bold_e}")
  print(f"Total number of hole groups: {len(topology.holes_groups)}")
  total_instances = 0
  for hole_group in topology.holes_groups:
    total_instances += len(hole_group.centers)
  print(f"Total number of instances: {total_instances}\n")


  for group_index, group in enumerate(topology.holes_groups):
    group.print(group_index+1)
  print("\n______________________________________________________")
  print("******************** NEW TOPOLOGY ********************")
  print("______________________________________________________\n")

