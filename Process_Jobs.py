from MACs_Conversions import rotation_translation, transform_points, compare_coordinates
from Utilities_and_Cosmetics import topology_sort
from Classes import Topology

# Global Variables
drilling_types = ["NC_DRILL_OLD", "NC_DRILL_DEEP", "NC_THREAD", "NC_DRILL_HR", "NC_JOB_MW_DRILL_5X"]


def extract_coordinates(holes_group_info, job_type, rotation_mat, translation_vec):
  """
  This function extracts holes centers (x,y,z) coordinates from a job.
  It extracts the hole centers depending on the job's type given.

  Args:
    holes_group_info (dict): Holes group information
    job_type (str):          Type of job

  Returns:
    new_coordinates (set): Coordinates extracted from the job
  """

  if job_type in drilling_types:
    holes_positions = holes_group_info['_tech_positions']

    # Defining a set with the holes centers - each hole center is (x,y,z) coordinates
    if holes_group_info["_positions_format"] == "VFrmt_P3Str_P3End_V3Dir":
      # For this position format, take only the first 3 values (out of 9) of each point
      new_coordinates = [holes_positions[i:i + 3] for i in range(0, len(holes_positions), 9)]

    elif holes_group_info["_positions_format"] == "VFrmt_XY":
      # For XY position format, take (x,y) values and set 'z' to the geometry's upper level.
      new_coordinates = {(round(holes_positions[i], 3),
                          round(holes_positions[i + 1], 3),
                          round(holes_group_info["_geom_upper_level"], 3)) for i in range(0, len(holes_positions), 2)}
    else:
      print("Haven't encountered this format yet. Need to check it out")  # Debugging purposes


  # elif job_type == 'NC_CHAMFER' or job_type == "NC_PROFILE":
  #   new_coordinates = {(round(vals[i], 3),
  #                       round(vals[i+1], 3),
  #                       0) for i in range(0, len(vals), 3)}

  # elif job_type == 'NC_PROFILE':
  #   new_coordinates = {(round(vals[i], 3),
  #                       round(vals[i+1], 3),
  #                       0) for i in range(0, len(vals), 3)}


  # Transforming the points to the CAD coordinate system origin
  new_coordinates = transform_points(new_coordinates, rotation_mat, translation_vec)
  return new_coordinates


def process_drilling_jobs(job, job_number, job_type, part_name, topologies_dict):
  """
  This function processes ONLY the jobs that involve drilling:
  1. It creates topologies.
  2. Assigns hole group to the relevant topologies.
  3. Assigns jobs to the relevant hole group.

  Args:
    job:              The operation (job) that is done on the stock material.
    job_number:       The job's number by the order it is defined on SolidCAM.
    job_type:         The job's type - drilling or non-drilling
    part_name:        The name of the part.
    topologies_dict:  A dictionary that maps topology names to topology objects.
  """

  # Calculating the Rotation Matrix and Translation Vector for each job
  rotation_mat, translation_vec = rotation_translation(job['home_matrix'])

  # Loops on the holes groups in each job
  for holes_group_info in job['geometry']["recognized_holes_groups"]:
    new_coordinates = extract_coordinates(holes_group_info, job_type, rotation_mat, translation_vec)

  # # Loops on the holes groups in each job
  # for holes_group_info in job['geometry']["recognized_holes_groups"]:
  #   # Saving all the hole positions
  #   holes_positions = holes_group_info['_tech_positions']
  #
  #   # Defining a set with the holes centers - each hole center is (x,y,z) coordinates
  #   if holes_group_info["_positions_format"] == "VFrmt_P3Str_P3End_V3Dir":
  #     # For this position format, take only the first 3 values (out of 9) of each point
  #     new_coordinates = [holes_positions[i:i+3] for i in range(0, len(holes_positions), 9)]
  #
  #   elif holes_group_info["_positions_format"] == "VFrmt_XY":
  #     # For XY position format, take (x,y) values and set 'z' to the geometry's upper level.
  #     new_coordinates = {(round(holes_positions[i], 3),
  #                         round(holes_positions[i+1], 3),
  #                         round(holes_group_info["_geom_upper_level"], 3)) for i in range(0, len(holes_positions), 2)}
  #   else:
  #     print("Haven't encountered this format yet. Need to check it out")   # Debugging purposes

    # # Transforming the points to the CAD coordinate system origin
    # new_coordinates = transform_points(new_coordinates, rotation_mat, translation_vec)
    # # print(f"new drilling coordinates: {{{', '.join(f'({x}, {y}, {z})' for x, y, z in new_coordinates)}}}")  # For debugging


    # Checking if the topology type is a valid string, and Cosmetics
    topology = topology_sort(holes_group_info["_topology_type"])
    topology_mask = holes_group_info["_geomShapeMask"]  # Saving the mask
    if topology == False:
      break
    # if it's the first time encountering that topology, create new Topology instance
    if topology not in topologies_dict:
      topologies_dict[topology] = Topology(topology, topology_mask)

    # Saving the hole's group geometry shape
    geom_shape = holes_group_info["_geom_ShapePoly"]
    # If it's the first time encountering that geometry shape & holes, add it
    holes_group, new_group_flag = topologies_dict[topology].add_hole_group(job, new_coordinates, geom_shape)

    # Adding the job to hole group
    holes_group.add_job(job, True, job['type'], job['tool']['tool_type'], job['tool'], job['job_depth'], new_coordinates, job_number)

    # If it's a new hole group, we initialize its parameters
    if new_group_flag:
      holes_group.update_parameters(holes_group_info, part_name)



# def process_non_drilling_jobs(job, job_number, topologies_dict):
#   """
#   This function processes all the jobs that DO NOT involve drilling.
#   Important to note - jobs are assigned to the relevant hole group ONLY if that
#   hole group already exists. I check whether a group exists by a bit intricate comparing
#   of coordinates.
#   """
#
#   new_coordinates = set()
#
#   # Checking if poly_arcs field exists, and if it's not None
#   if "poly_arcs" in job['geometry'] and job['geometry']['poly_arcs'] is not None:
#     # Going over on each element in poly_arcs - each element represent a
#     for arc_group in job['geometry']['poly_arcs']:
#       for arc in arc_group:
#         if arc["type"] == "arc":
#           new_coordinates.add((round(arc["c"][0]),
#                                round(arc["c"][1]),
#                                round(holes_group_info["_geom_upper_level"]))
#
#     new_coordinates = transform_points(arc, rotation_mat, translation_vec)
#
#
#     # Calculating the Rotation Matrix and Translation Vector for each job
#     rotation_mat, translation_vec = rotation_translation(job['home_matrix'])
#
#     # Defining a set with the holes centers - each hole center is (x,y,z=0) coordinates
#     new_coordinates = {(round(vals[i], 3),
#                         round(vals[i + 1], 3),
#                         0) for i in range(0, len(vals), 3)}
#     # Transforming the points to the CAD coordinate system origin
#     new_coordinates = transform_points(new_coordinates, rotation_mat, translation_vec)
#     # print(f"new NON drilling coordinates: {{{', '.join(f'({x}, {y}, {z})' for x, y, z in new_coordinates)}}}")  # For debugging
#
#     # Assigning jobs to holes via "vals" field
#     for key, topology in topologies_dict.items():  # Going over all the topologies
#       for
#     group in topology.holes_groups:  # Going over all the holes groups inside each topology
#     for existing_job in group.jobs:  # Going over all the jobs inside each hole group
#       for
#     new_center in new_coordinates:  # Going over all holes in the CURRENT job
#     # If true, the center in the current job belongs to an existing hole group, then we try to assign the current job to this hole group.
#     # If false, this job doesn't work on any existing hole group, so we don't try to assign it
#     if not compare_coordinates(new_center, existing_job.centers, group.hole_depth,
#                                job["home_number"], existing_job.parallel_home_numbers):
#     # Adding the job only if it's the first time encountered
#       group.add_job(job, False, job['type'], job['tool']['tool_type'], job["tool"], job['job_depth'],
#                     new_coordinates, job_number)




def process_non_drilling_jobs(job, job_number, topologies_dict):
  """
  This function processes all the jobs that DO NOT involve drilling.
  Important to note - jobs are assigned to the relevant hole group ONLY if that
  hole group already exists. I check whether a group exists by a bit intricate comparing
  of coordinates.
  """
  # Checking if vals field exists

  if "vals" in job['geometry']:
    vals = job['geometry']['vals']

    # Calculating the Rotation Matrix and Translation Vector for each job
    rotation_mat, translation_vec = rotation_translation(job['home_matrix'])

    # Defining a set with the holes centers - each hole center is (x,y,z=0) coordinates
    new_coordinates = {(round(vals[i], 3),
                        round(vals[i+1], 3),
                        0) for i in range(0, len(vals), 3)}
    # Transforming the points to the CAD coordinate system origin
    new_coordinates = transform_points(new_coordinates, rotation_mat, translation_vec)
    # print(f"new NON drilling coordinates: {{{', '.join(f'({x}, {y}, {z})' for x, y, z in new_coordinates)}}}")  # For debugging

    # Assigning jobs to holes via "vals" field
    for key, topology in topologies_dict.items():  # Going over all the topologies
      for group in topology.holes_groups:          # Going over all the holes groups inside each topology
        for existing_job in group.jobs:            # Going over all the jobs inside each hole group
          for new_center in new_coordinates:       # Going over all holes in the CURRENT job
            # If true, the center in the current job belongs to an existing hole group, then we try to assign the current job to this hole group.
            # If false, this job doesn't work on any existing hole group, so we don't try to assign it
            if not compare_coordinates(new_center, existing_job.centers, group.hole_depth,
                              job["home_number"], existing_job.parallel_home_numbers):
              # Adding the job only if it's the first time encountered
              group.add_job(job, False, job['type'], job['tool']['tool_type'], job["tool"], job['job_depth'], new_coordinates, job_number)


