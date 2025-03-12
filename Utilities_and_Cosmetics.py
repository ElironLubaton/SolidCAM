import json
import re
from enum import Enum

# Global Variables
drilling_types = ["NC_DRILL_OLD", "NC_DRILL_DEEP", "NC_THREAD", "NC_DRILL_HR", "NC_JOB_MW_DRILL_5X"]
non_drilling_types = ["NC_PROFILE", "NC_CHAMFER"]


# A function for reading JSON files
def read_json(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data



def process_job_name(job_type):
    """ A function for cosmetic purposes """
    if job_type == "NC_DRILL_OLD":
        return "2_5D_Drilling"
    elif job_type == "NC_PROFILE":
        return "Profile"
    elif job_type == "NC_CHAMFER":
        return "Chamfer"
    elif job_type == "NC_DRILL_DEEP":
        return "Multi_Depth_Drilling"
    elif job_type == "NC_THREAD":
        return "Thread_Milling"
    elif job_type == "NC_DRILL_HR":
        return "Drill_Recognition"
    elif job_type == "NC_JOB_MW_DRILL_5X":
        return "Multi Axis Drilling"
    else:
        return job_type


def process_tool_type_name(tool_type):
    """ A function for cosmetic purposes - deletes prefix, and lowercases """
    # split the string by underscores
    words = tool_type.split('_')
    # remove prefix, and capitalize the first letter of each word and lowercase the rest
    processed_words = [word.capitalize() for word in words[1:]]
    # Join the words back with underscores
    return '_'.join(processed_words)


def topology_sort(topology_type):
    # Checking if the topology type is a valid string
    if len(topology_type) == 0:
        return False
    else:
        # Cosmetics - using [5:] in order to remove 'HR_hw' prefix
        topology_type = topology_type[5:]

        # Cosmetics - adding underscores between capital letters
        return re.sub(r'(?<!^)(?=[A-Z])', '_', topology_type)


class Mask(Enum):
    """
    This class is used to deal with JSON's field '_geomShapeMask' - this field
    holds a vector of numbers that defines the topology of a hole, but not the
    hole's dimensions. The humber are written Right to Left (as in Hebrew).
    Each number in the mask tells us the shape of the segments composing the hole.
    """

    PLANE = 1
    CYLINDER = 2
    CONIC = 3
    CHAMFER = 4

    # I can access the strings by using: "Mask(number 1-4).name"


def validate_job(job):
    """
    This function purpose is for verifying that all the JSON fields that are being used are either:
    1 - Existing
    2 - Not None
    3 - Bigger than 0

    *Note - the order of the fields on this code are similar to the order of the fields on the JSON

    Args:
        job (dict): Holds all the fields of the job
    """

    errors = []           # A list that will keep all the invalid lines
    job_type = None       # A string that will keep the job's type

    # Checking the fields that are common to every job
    if job.get("home_matrix") is None or len(job["home_matrix"])!=16:
        errors.append("home matrix field is invalid")                     # Checking if home_matrix contain 16 values
    if job.get("job_depth") is None:
        errors.append("job depth field is invalid")                       # Checking job_depth field
    if job.get("name") is None:
        errors.append("name field is invalid")                            # Checking name field

    if job.get("tool") is None:
        errors.append("tool field is invalid")                            # Checking tool field
    else:
        tool_subfields = ["lengthParameters", "parameters", "tool_type"]  # Checking subfields of tool
        for tool_subfield in tool_subfields:
            if job["tool"].get(tool_subfield) is None:
                errors.append(f"{tool_subfield} field is invalid")

    if job.get("type") is None:
        errors.append("type field is invalid")                            # Checking type field
    else:
        job_type = job.get("type")

    # True if it's one of the Drilling jobs - they all should have valid 'drill' field
    if job_type in drilling_types:
        if job.get("drill") is None or len(job.get("drill")) == 0:
            errors.append("drill field is invalid")                        # Checking drill field

    # Checking 'geometry' field and many of his subfields
    if job.get("geometry") is None:
        errors.append("geometry field is invalid")                          # Checking geometry field
    else:
        # True if it's Profile or Chamfer job - they should have a valid 'poly_arcs' field
        if job_type in non_drilling_types:
            geometry = job["geometry"]
            if geometry.get("poly_arcs") is None or len(geometry.get("poly_arcs"))==0:   # Checking poly_arcs field
                errors.append("geometry.poly_arcs field is invalid")

        if job["geometry"].get("recognized_holes_groups") is None:                        # Checking recognized_holes_groups field
            errors.append("recognized_holes_groups field is invalid OR it's a pre-drilling operation")
        else: # Going over on all the holes groups in the job
            for holes_group_info in job['geometry']["recognized_holes_groups"]:

                # Checking if the following fields are not None
                fields_not_none = ["_geom_depth", "_geom_thread_depth", "_geom_thread_hole_diameter", "_geom_thread_pitch", "_geom_upper_level"]
                for field in fields_not_none:
                    if holes_group_info.get(field) is None:
                        errors.append(f"{field} field is invalid")

                # Checking if the following fields are not None nor equals 0
                if holes_group_info.get("_geomShapeMask") is None or holes_group_info.get("_geomShapeMask")<=0:
                    errors.append(f"_geomShapeMask field is invalid")

                fields_not_none_or_zero = ["_geom_ShapePoly", "_positions_format", "_topology_type"]
                for field in fields_not_none_or_zero:
                    if holes_group_info.get(field) is None or len(holes_group_info.get(field)) == 0:
                        errors.append(f"{field} field is invalid")

                # Checking _tech_positions field - it should contain at least 2 elements
                if holes_group_info.get("_tech_positions") is None or len(holes_group_info.get("_tech_positions"))<2:
                    errors.append("_tech_positions field is invalid")

                # True if it's a Multi-Axis drilling job
                if job_type == "NC_JOB_MW_DRILL_5X":
                    if holes_group_info.get("_tech_depth") is None:
                        errors.append("_tech_depth field is invalid")          # Checking _tech_depth field
                    if holes_group_info.get("_tech_depth_type") is None or len(holes_group_info.get("_tech_depth_type"))==0:
                        errors.append("_tech_depth_type field is invalid")     # Checking _tech_depth_type field
                    if holes_group_info.get("_tech_depth_type_val") is None:
                        errors.append("_tech_depth_type_val field is invalid") # Checking _tech_depth_type_val field

                # todo This part regards Thread Milling, and I'm not sure if other jobs other than NC_THREAD should have this field not NULL
                # True if it's a Thread Milling Job
                elif job_type == "NC_THREAD":
                    if job.get("thread_mill") is None or len(job.get("thread_mill")) == 0:
                        errors.append("thread_mill field is invalid")

                    # Checking again the thread fields, but also checking if their value is not zero
                    fields_not_none = ["_geom_thread_depth", "_geom_thread_diameter", "_geom_thread_pitch"]
                    for field in fields_not_none:
                        if holes_group_info.get(field) is None or len(holes_group_info.get(field)) == 0:
                            errors.append(f"{field} field is invalid")

    # Printing the errors if there are any
    if errors:
        print("\n\n")
        print(f"Job name: {job['name']}")
        for error in errors:
            print(error)
        print("\n\n")