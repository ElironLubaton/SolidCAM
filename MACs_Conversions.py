import numpy as np

# Used in order to compare between coordinates of centers of holes.
# It is required because the field "_tech_positions" values should be equal to the field 'vals'
# values, but they are only approximately close.
tolerance = 0.111


def rotation_translation(home_matrix):
    """
    This function extracts the Rotation Matrix and the Translation Vector from
    the home_matrix in the JSON.
    Both of them were computed with regard to the CAD coordinate system origin.

    *Notes:
      1 - We transpose the rotation matrix we got from home_matrix.
      2 - We disregard the last 4 elements in home_matrix.

    Args:
      home_matrix: A 16x1 list that contains the values of rotation and translation.

    Returns two elements:
      Rotation matrix -    3x3 numpy array.
      Translation vector - 3x1 numpy array.
    """
    # Extracting the rotation matrix values
    r_x = np.array(home_matrix[0:3])
    r_y = np.array(home_matrix[4:7])
    r_z = np.array(home_matrix[8:11])
    rotation_mat = np.array([r_x, r_y, r_z]).T

    # # Used if we want to convert from inch to mm
    # # Computing translation vector by refer to CAD model origin
    # if is_inch:  # converting to mm if needed
    #   translation_vec = np.array([inches_to_mm(home_matrix[3]),
    #                               inches_to_mm(home_matrix[7]),
    #                               inches_to_mm(home_matrix[11])]).reshape(3,1)
    # else:
    #   translation_vec = np.array([home_matrix[3], home_matrix[7], home_matrix[11]]).reshape(3,1)

    # Extracting the translation vector values
    translation_vec = np.array([home_matrix[3], home_matrix[7], home_matrix[11]]).reshape(3, 1)

    return rotation_mat, translation_vec


def extract_coordinates(holes_group_info, rotation_mat, translation_vec):
    """
    This function extracts holes centers (x,y,z) coordinates from a job.
    It extracts the hole centers depending on the job's type given.

    Args:
      holes_group_info (dict):   Holes group information
      rotation_mat (np.arr):     Rotation matrix from MAC to CAD origin
      translation_vec (np.arr):  Translation vector from MAC to CAD origin

    Returns:
      new_coordinates (set): Coordinates extracted from the job
    """

    holes_positions = holes_group_info['_tech_positions']

    # Defining a set with the holes centers - each hole center is (x,y,z) coordinates
    # For this position format, take only the first 3 values (out of 9) of each point
    if holes_group_info["_positions_format"] == "VFrmt_P3Str_P3End_V3Dir":
        new_coordinates = [holes_positions[i:i + 3] for i in range(0, len(holes_positions), 9)]

    # For XY position format, take (x,y) values and set 'z' to the geometry's upper level.
    elif holes_group_info["_positions_format"] == "VFrmt_XY":
        new_coordinates = {(round(holes_positions[i], 3),
                            round(holes_positions[i + 1], 3),
                            round(holes_group_info["_geom_upper_level"], 3)) for i in range(0, len(holes_positions), 2)}
    # Debugging purposes
    else:
        print("Haven't encountered this format yet. Need to check it out")
        raise ValueError("Invalid position format.")

    # Transforming the points to the CAD coordinate system origin
    new_coordinates = transform_points(new_coordinates, rotation_mat, translation_vec)
    return new_coordinates


def transform_points(coordinates, rotation_mat, translation_vec):
    """
    This function transforms hole center (x,y,z) coordinates from any coordinate
    system to the CAD model coordinate system:
    1 - Translation - Subtracting the translation vector from the hole center coordinates.
    2 - Rotation -    Dot product of the rotation matrix with the hole center coordinates.

    Args:
      coordinates:     Set with tuples of (x,y,z) centers of holes.
      rotation_mat:    3x3 np array of the Rotation Matrix.
      translation_vec: 3x1 np array of the Translation Vector.

    Returns:
      A set of the transformed points to the CAD model coordinate system
    """
    transformed_coordinates = set()

    for point in coordinates:
        # Convert the point to a numpy array (x, y, z)
        point_array = np.array([[point[0]], [point[1]], [point[2]]]).reshape(3, 1)

        # Applying translation
        transformed_point = point_array - translation_vec
        # Applying rotation
        transformed_point = np.dot(rotation_mat, transformed_point)

        # Convert the transformed point to a tuple, round it, and add it to the set
        transformed_coordinates.add((round(transformed_point[0, 0], 3),
                                     round(transformed_point[1, 0], 3),
                                     round(transformed_point[2, 0], 3)))
    return transformed_coordinates



def compare_geom_distances(new_geometry, existing_geometry):
    """
    Compare two _geom_ShapePoly lists to check if they are identical.
    They are considered identical if, for each corresponding element:
    - (p0[0] - p1[0]) is equal in both polys
    - (p0[1] - p1[1]) is equal in both polys

    Args:
        new_geometry (list): List of dicts containing the hole's description of the geometry we check
        existing_geometry(list): List of dicts containing the hole's description of an existing geometry we compare to

    Returns:
        True  if identical - geom_ShapePoly distances are equal
        False otherwise
    """
    for elem1, elem2 in zip(new_geometry, existing_geometry):
        delta_x1 = elem1['p0'][0] - elem1['p1'][0]
        delta_x2 = elem2['p0'][0] - elem2['p1'][0]
        delta_y1 = elem1['p0'][1] - elem1['p1'][1]
        delta_y2 = elem2['p0'][1] - elem2['p1'][1]

        if not (abs(delta_x1 - delta_x2) < tolerance and abs(delta_y1 - delta_y2) < tolerance):
            return False  # Found a mismatch

    return True  # All deltas matched


def compare_geometries(new_geometry, existing_geometry, job_number):
    """
    This function compares the shape of two geometries ("_geom_ShapePoly" field).
    We make a straight-forward comparison, and if that doesn't work we compare
    the REVERSE of the geometry.

    *Note - This function is used in order to deal with cases where a hole
    is being worked from different MACs (which are parallel).

    The Algorithm:
    1 - Straight-forward comparison.
    2 - If True, then geometry already exist.
    3 - If False, Check if both geometries contain the same number of elements:
        - If False - the geometries are NOT the same, so return False.
        - If True  - then proceed to check if they are the same.
    4 - REVERSE the order of the elements in the geometry list we're checking
    5 - Check both lists with elements "head to head":
      5.1 - Compare the types of the elements
      5.2 - Compare the diameter of the elements
      5.3 - Compare the depth of the elements
    6 - If we passed 5, then geometry already exists

    Args:
      new_geometry: List of dictionaries containing the hole's description of the geometry we check
      existing_geometry: List of dictionaries containing the hole's description of an existing geometry we compare to
      geom_upper_level (int): Containing the upper level of the geometry of the hole
      job_number(int): Containing the job's number (for Debugging purposes)

    Returns:
      True  if the new geomtry and existing geometry are the same
      False if the new geomtry and existing geometry are NOT the same
    """

    # 1,2 - Straight-forward comparison. If true, then geometry already exists.
    if new_geometry == existing_geometry or compare_geom_distances(new_geometry, existing_geometry):
        return True

    # 3 - Checking if both lists contain the same number of elements
    # If true, that proceed to check if they are the same, else, the geometries are NOT the same, so return False
    if len(new_geometry) != len(existing_geometry):
        return False

    # 4 - Reversing the order of the elements in the new_geometry
    # We do this in order to check if it's the same geometry represented from parallel home MACs
    new_geometry.reverse()
    if compare_geom_distances(new_geometry, existing_geometry):
        return True

    # 5 - Going over the elements "Head to Head" (from hebrew...)
    for i in range(len(new_geometry)):
        # 5.1 - If the types are different, the geometries are NOT the same
        if new_geometry[i]["type"] != existing_geometry[i]["type"]:
            # if job_number in [55, 62]:                                       # DEBUGGING PURPOSES
            #     print(f"Job number is: {job_number} - types are different")  # DEBUGGING PURPOSES
            #     print(f"New geometry is: {new_geometry}")                    # DEBUGGING PURPOSES
            #     print(f"Existing geometry is: {new_geometry}")               # DEBUGGING PURPOSES
            return False
        else:
            # 5.2 - Checking if the diameters are the same. If not, then geometries are NOT the same
            if new_geometry[i]["p0"][0] != existing_geometry[i]["p1"][0]:
                # if job_number in [55, 62]:                                          # DEBUGGING PURPOSES
                #     print(f"Job number is: {job_number} - diameters are different") # DEBUGGING PURPOSES
                #     print(f"New geometry is: {new_geometry}")                       # DEBUGGING PURPOSES
                #     print(f"Existing geometry is: {new_geometry}")                  # DEBUGGING PURPOSES
                return False

            # 5.3 - Checking if the depths are the same. If not, then geometries are NOT the same
            new_geom_depth = abs(new_geometry[i]["p0"][1] - new_geometry[i]["p1"][1])
            existing_geom_depth = abs(existing_geometry[i]["p0"][1] - existing_geometry[i]["p1"][1])
            if abs(new_geom_depth - existing_geom_depth) > tolerance:
                # if job_number in [55, 62]:                                      # DEBUGGING PURPOSES
                #     print(f"Job number is: {job_number} - depth are different") # DEBUGGING PURPOSES
                #     print(f"New geometry is: {new_geometry}")                   # DEBUGGING PURPOSES
                #     print(f"Existing geometry is: {new_geometry}")              # DEBUGGING PURPOSES
                return False
    # If we got here, then geometries are the same
    return True




# def compare_coordinates(new_center, existing_centers, hole_depth, home_number, parallel_home_numbers):
#     """
#     This function compares (x,y,z) points in order to discern if two hole centers
#     refer to the SAME hole by using the following conditions:
#     1 - If the two holes centers (x,y,z) coordinates are the same.
#     2 - If the distance between the two holes centers equals the hole's depth.
#
#     *Note - This function is used in order to deal with cases where a hole is being worked
#      different MACs (which are parallel).
#
#     Args:
#       new_center: Tuple containing the center we're checking.
#       existing_centers: Set containing the hole's group exisiting centers.
#       hole_depth: Int containing the hole's depth
#       home_number: Int containing the new job's home number
#       parallel_home_numbers: List containing the existing job parallel home numbers
#
#     Returns:
#       True if the two hole centers refer to DIFFERENT holes, and the new_center coordinates
#       False if the two hole centers refer to the SAME hole.
#     """
#     # 1 - Checking if the exact same coordinates already exist
#     if new_center in existing_centers:
#         return False, new_center
#
#     # Going over on all the existing points in the hole group
#     for existing_center in existing_centers:
#         # Checking if the home numbers are parallel
#         if home_number in parallel_home_numbers:
#             # Checking if the distance between the centers equals the hole's depth
#             centers_distance = np.linalg.norm(np.array(new_center) - np.array(existing_center))
#             # If true, the two centers refer to the same hole, so return False
#             if abs(centers_distance - hole_depth) <= tolerance:
#                 return False, existing_center
#
#     return True, None


def compare_coordinates(new_center, existing_group, home_number, hole_depth, job_number):
    """
    This function compares (x,y,z) points in order to discern if two hole centers
    refer to the SAME hole by using the following conditions:
    1 - If the two holes centers (x,y,z) coordinates are the same.
    2 - If the distance between the two holes centers equals the hole's depth.

    *Note - This function is used in order to deal with cases where a hole is being worked
     different MACs (which are parallel).

    Args:
      new_center: Tuple containing the center we're checking.
      existing_group: HoleGroup object containing all the Hole objects we check.
      hole_depth: Int containing the hole's depth
      home_number: Int containing the new job's home number
      job_number(int): Int containing the job's number (for Debugging purposes)

    Returns:
      True if the two hole centers refer to the SAME hole, and the existing hole object.
      False if the two hole centers refer to DIFFERENT holes.
    """

    hole_exist_flag = False

    # 1 - Checking if the exact same coordinates already exist
    if new_center in existing_group.centers:
        # If true, the two centers refer to the same hole, so return True
        # if job_number in [55, 62]:                                                     # DEBUGGING PURPOSES
        #     print(f"Job number is: {job_number} - the exact same coordinates exists")  # DEBUGGING PURPOSES
        hole_exist_flag = True
        return hole_exist_flag, existing_group.holes[new_center]

    # Going over on all the Hole objects in that hole group
    for existing_center in existing_group.centers:
        # Going over on all the jobs inside each Hole object
        for existing_job in existing_group.holes[existing_center].jobs:
            # Check if home numbers are parallel
            if home_number in existing_job.parallel_home_numbers:
                # Checking if the distance between the centers equals the hole's depth
                centers_distance = np.linalg.norm(np.array(new_center) - np.array(existing_center))
                # If true, the two centers refer to the same hole, so return True
                if abs(centers_distance - hole_depth) <= tolerance:
                    # if job_number in [55, 62]:                                                 # DEBUGGING PURPOSES
                    #     print(f"Job number is: {job_number} - dist between centers == depth")  # DEBUGGING PURPOSES
                    hole_exist_flag = True
                    return hole_exist_flag, existing_group.holes[existing_center]

    # Return hole_exist_flag False if the two hole centers refer to DIFFERENT holes
    return hole_exist_flag, None



