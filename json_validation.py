""" This notebook's purpose is validating the JSON files of parts. """

import json
import os
import difflib
from Utilities_and_Cosmetics import read_json

# Directory path to the JSON files
dir_path = 'C:/Users/eliron.lubaton/Desktop/SolidCAM/CodePy/JSON'

drilling_types = ["NC_DRILL_OLD", "NC_DRILL_DEEP", "NC_THREAD", "NC_DRILL_HR", "NC_JOB_MW_DRILL_5X"]



"""## Verfication Functions"""

"""
This code goes over all the files and looks for invalid data:
1 - If a drilling technology is used BUT "drill" field is missing.
2 - If a "drill" field exists BUT there is no "recognized_holes_groups" field.
  * Important note - there are pre-drilling jobs for pockets that don't contain "recognized_holes_groups" field,
    and it's fine.
3 - If a "recognized_holes_groups" field exists, BUT "_topology_type" field is an empty string.


*** IMPORTANT NOTE:
If a job is classified as invalid, it is maybe because it is a pre-drilling for
a pocket, so until I'm sure the data collection tool works well, I have to check
these cases BY HAND.
"""

# These two lines used for printing with bold font
bold_s = '\033[1m'  # Start to write in bold
bold_e = '\033[0m'  # End to write in bold

for file_name in os.listdir(dir_path):
    if file_name.endswith('.json'):
        file_path = os.path.join(dir_path, file_name)

        # Read the JSON file
        data = read_json(file_path)
        # Printing the part's name
        print(f"{bold_s}Part name{bold_e}: {file_name}")

        valid_jobs_counter, total_jobs_counter = 0, 0

        invalid_jobs_number = []

        # Going over all the jobs in the file
        for job_number, job in enumerate(data["event_data"]["jobs"]):
            valid_flag = 1
            # Checking if a drilling technology is used
            if job["type"] in drilling_types:
            # if (job["type"] == "NC_DRILL_OLD" or job["type"] == "NC_DRILL_DEEP" or
            #         job["type"] == "NC_THREAD" or job["type"] == "NC_DRILL_HR" or
            #         job["type"] == "NC_JOB_MW_DRILL_5X"):
                total_jobs_counter += 1
                # Checking if a "drill" field exists
                if "drill" in job:
                    # Checking if a "recognized_holes_groups" field exists
                    if "recognized_holes_groups" in job['geometry']:
                        # Checking if 'topology_type field isn't empty string in all hole groups
                        for hole_group in job["geometry"]["recognized_holes_groups"]:
                            if len(hole_group['_topology_type']) > 0:
                                pass
                            else:
                                valid_flag = 0
                                invalid_jobs_number.append(job_number + 1)
                                print(
                                    f"'_topology_type' field is MISSING in job {job['name']}, number {job_number + 1}")
                    else:
                        valid_flag = 0
                        invalid_jobs_number.append(job_number + 1)
                        print(
                            f"'recognized_holes_groups' field is MISSING in job {job['name']}, number {job_number + 1}")
                else:
                    valid_flag = 0
                    invalid_jobs_number.append(job_number + 1)
                    print(f"'drill' field is MISSING in job {job['name']}, number {job_number + 1}")
            else:
                valid_flag = 0

            if valid_flag:
                valid_jobs_counter += 1

        # Printing how many jobs are valid out of total
        if len(invalid_jobs_number)>0:
            print(f"\nJobs Numbers: {invalid_jobs_number}")
        print(f"\nTotal valid drilling jobs: {valid_jobs_counter}/{total_jobs_counter}\n\n")


# @title Filtering files that don't contain "drill" field
def categorize_json_files(directory):
    with_drill = []
    without_drill = []

    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            filepath = os.path.join(directory, filename)
            with open(filepath, 'r') as file:
                try:
                    data = json.load(file)
                    # Navigate to event_data > jobs
                    jobs = data.get("event_data", {}).get("jobs", [])
                    # Check for the presence of "drill" in jobs
                    if any("drill" in job for job in jobs):
                        with_drill.append(filename)
                    else:
                        without_drill.append(filename)
                except (json.JSONDecodeError, KeyError):
                    print(f"Error processing file: {filename}")

    return with_drill, without_drill


# Example usage
directory = "/content/test"  # Replace with your directory containing the JSON files
with_drill, without_drill = categorize_json_files(directory)

print("Files with 'drill':", with_drill)
print("Files without 'drill':", without_drill)





