from MACs_Conversions import rotation_translation,  extract_coordinates
from Utilities_and_Cosmetics import topology_sort
from Classes import Topology

# Global Variables
drilling_types = ["NC_DRILL_OLD", "NC_DRILL_DEEP", "NC_THREAD", "NC_DRILL_HR", "NC_JOB_MW_DRILL_5X"]
non_drilling_types = ["NC_PROFILE", "NC_CHAMFER", "NC_JOB_HSS_PARALLEL_TO_CURVE"]


def process_jobs(job, part_name, topologies_dict):
    """
    This function processes jobs:
    1. It creates topologies.
    2. Assigns hole group to the relevant topologies.
    3. Assigns jobs to the relevant holes.

    Args:
      job:              The operation (job) that is done on the stock material.
      part_name:        The name of the part.
      topologies_dict:  A dictionary that maps topology masks to topology objects.
    """
    # Calculating the Rotation Matrix and Translation Vector for each job
    rotation_mat, translation_vec = rotation_translation(job['home_matrix'])

    # Loops on all elements in 'recognized_holes_groups' field - each represents a hole group
    for holes_group_info in job['geometry']["recognized_holes_groups"]:
        # Extracting the coordinates based on the coordinates format
        new_coordinates = extract_coordinates(holes_group_info, rotation_mat, translation_vec)

        # Checking if the topology type is a valid string, and Cosmetics
        topology_type = topology_sort(holes_group_info["_topology_type"])
        # Saving the mask - a set of number that defines the topology
        topology_mask = int(holes_group_info["_geomShapeMask"])
        # True if 'topology_type' is an empty string
        if topology_mask<=0:
            print(f"Topology mask is NOT valid")
            break

        # Saving the reversed topology mask
        reversed_topology_mask = int(str(topology_mask)[::-1])
        # Checking if the mask or its reverse already exist. If true, create new Topology instance
        if topology_mask not in topologies_dict and reversed_topology_mask not in topologies_dict:
            topologies_dict[topology_mask] = Topology(topology_type, topology_mask)
        # If got here, then checking if the reverse mask already exists - If true, then save the reversed mask
        elif reversed_topology_mask in topologies_dict:
            topology_mask = reversed_topology_mask

        # If it's the first time encountering that geometry shape & holes, add it
        topologies_dict[topology_mask].add_hole_group(job, new_coordinates, holes_group_info, part_name)






# def process_non_drilling_jobs(job, topologies_dict):
#   """
#   This function processes all the jobs that DO NOT involve drilling.
#   Important to note - jobs are assigned to the relevant hole group ONLY if that
#   hole group already exists. I check whether a group exists by a bit intricate comparing
#   of coordinates.
#   """
#   # Checking if vals field exists
#
#   if "vals" in job['geometry']:
#     vals = job['geometry']['vals']
#
#     # Calculating the Rotation Matrix and Translation Vector for each job
#     rotation_mat, translation_vec = rotation_translation(job['home_matrix'])
#
#     # Defining a set with the holes centers - each hole center is (x,y,z=0) coordinates
#     new_coordinates = {(round(vals[i], 3),
#                         round(vals[i+1], 3),
#                         0) for i in range(0, len(vals), 3)}
#     # Transforming the points to the CAD coordinate system origin
#     new_coordinates = transform_points(new_coordinates, rotation_mat, translation_vec)
#     # print(f"new NON drilling coordinates: {{{', '.join(f'({x}, {y}, {z})' for x, y, z in new_coordinates)}}}")  # For debugging
#
#     # Assigning jobs to holes via "vals" field
#     for key, topology in topologies_dict.items():  # Going over all the topologies
#       for group in topology.holes_groups:          # Going over all the holes groups inside each topology
#         for existing_job in group.jobs:            # Going over all the jobs inside each hole group
#           for new_center in new_coordinates:       # Going over all holes in the CURRENT job
#             # If true, the center in the current job belongs to an existing hole group, then we try to assign the current job to this hole group.
#             # If false, this job doesn't work on any existing hole group, so we don't try to assign it
#             if not compare_coordinates(new_center, existing_job.centers, group.hole_depth,
#                               job["home_number"], existing_job.parallel_home_numbers):
#               # Adding the job only if it's the first time encountered
#               group.add_job(job, new_coordinates)


# def process_drilling_jobs(job, part_name, topologies_dict):
#   """
#   This function processes ONLY the jobs that involve drilling:
#   1. It creates topologies.
#   2. Assigns hole group to the relevant topologies.
#   3. Assigns jobs to the relevant hole group.
#
#   Args:
#     job:              The operation (job) that is done on the stock material.
#     part_name:        The name of the part.
#     topologies_dict:  A dictionary that maps topology names to topology objects.
#   """
#
#   # Calculating the Rotation Matrix and Translation Vector for each job
#   rotation_mat, translation_vec = rotation_translation(job['home_matrix'])
#   job_type = job["type"] # Saving the type of the Job
#
#   # Loops on the holes groups in each job
#   for holes_group_info in job['geometry']["recognized_holes_groups"]:
#     new_coordinates = extract_coordinates(holes_group_info, rotation_mat, translation_vec)
#
#     # Checking if the topology type is a valid string, and Cosmetics
#     topology = topology_sort(holes_group_info["_topology_type"])
#     # True if 'topology_type' is an empty string
#     if not topology:
#       print(f"Topology type is NOT valid")
#       break
#     # if it's the first time encountering that topology, create new Topology instance
#     if topology not in topologies_dict:
#       topology_mask = holes_group_info["_geomShapeMask"]  # Saving the mask
#       topologies_dict[topology] = Topology(topology, topology_mask) # Creating a new instance of Topology
#
#     # Saving the hole's group geometry shape
#     geom_shape = holes_group_info["_geom_ShapePoly"]
#     # If it's the first time encountering that geometry shape & holes, add it
#     holes_group, new_group_flag = topologies_dict[topology].add_hole_group(job, new_coordinates, geom_shape, holes_group_info, part_name)
#
#     # Adding the job to hole group
#     holes_group.add_job(job, new_coordinates, holes_group_info)








# I didn't continue this function because I'm waiting for Tatyana to add recognized_holes_groups for
# Profile and Chamfer jobs - I want to take the 'z' value for each hole center from the field
# _geom_upper_level, which is inside recognized_holes_groups field

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


