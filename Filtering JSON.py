# @title Deleting Unneccesary Fields

import json
import os

"""
This function is used for deleting fields that I find unneccesary at the moment.
"""

def clean_json_file(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)

    jobs = data["event_data"]["jobs"]

    # Fields to remove from each job
    fields_to_remove = [
        "coolant", "ver", "usage_index", "job_group_name", "job_holeWzrd_id",
        "job_is_from_HR", "toolPath"
    ]

    # Go through each job and remove the specified fields
    for job in jobs:
        # Remove fields from job
        for field in fields_to_remove:
            if field in job:
                del job[field]
        # Add "separator" field at the end of each job
        job["separator"] = "____________________________________________________________________________________________"

    # Save the modified JSON back to the file
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

# Example usage
directory = 'C:/Users/eliron.lubaton/Desktop/SolidCAM/CodePy/JSON'

# Iterate through each JSON file in the directory
for filename in os.listdir(directory):
    if filename.endswith('.json'):
        file_path = os.path.join(directory, filename)
        clean_json_file(file_path)
        print(f"Processed {filename}")