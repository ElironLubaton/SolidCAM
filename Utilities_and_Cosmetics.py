import json
import re
from enum import Enum


# A function for reading JSON files
def read_json(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data


def process_job_name(job_type):
  """ A function for cosmetic purposes """
  if   job_type == "NC_DRILL_OLD":       return "2_5D_Drilling"
  elif job_type == "NC_PROFILE":         return "Profile"
  elif job_type == "NC_DRILL_DEEP":      return "Multi_Depth_Drilling"
  elif job_type == "NC_THREAD":          return "Thread_Milling"
  elif job_type == "NC_DRILL_HR":        return "Drill_Recognition"
  elif job_type == "NC_JOB_MW_DRILL_5X": return "Multi Axis Drilling"
  else:                                  return job_type


def process_tool_type_name(tool_type):
  """ This function's purpose is for cosmetics - deletes prefix, and lowercases """
  # split the string by underscores
  words = tool_type.split('_')
  # remove prefix, and capitalize the first letter of each word and lowercase the rest
  processed_words = [word.capitalize() for word in words[1:]]
  # Join the words back with underscores
  return '_'.join(processed_words)


def topology_sort(topology_type):
  # Checking if the topology type is a valid string
  if len(topology_type)==0:
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