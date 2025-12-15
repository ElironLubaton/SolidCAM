import json
import os
import re
import math
from enum import Enum
from types import NoneType

# Global Variables
drilling_types = ["NC_DRILL_OLD", "NC_DRILL_DEEP", "NC_THREAD", "NC_DRILL_HR", "NC_JOB_MW_DRILL_5X"]
non_drilling_types = ["NC_PROFILE", "NC_CHAMFER", "NC_JOB_HSS_PARALLEL_TO_CURVE"]


# A function for reading JSON files
def read_json(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data



def process_job_name(job_type: str) -> str:
    """
    A function for cosmetic purposes.
    It gets the "job_type" field from the JSON file and make it more readable
    """
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
        return "Multi_Axis_Drilling"
    elif job_type == "NC_JOB_HSS_PARALLEL_TO_CURVE":
        return "HSS_Parallel_to_Curve"
    else:
        return job_type


def process_tool_type_name(tool_type: str) -> str:
    """ A function for cosmetic purposes - deletes prefix, and lowercases """
    # split the string by underscores
    words = tool_type.split('_')
    # remove prefix, and capitalize the first letter of each word and lowercase the rest
    processed_words = [word.capitalize() for word in words[1:]]
    # Join the words back with underscores
    return '_'.join(processed_words)


def remove_non_ascii(text: str) -> str:
    """ Remove non-ascii characters from a string """
    return text.encode('ascii', 'ignore').decode()


def topology_sort(topology_type: str):
    """ A function for validation and cosmetics purposes """
    # Checking if the topology type is a valid string
    if len(topology_type) == 0:
        return False
    else:
        # Cosmetics - removing 'HR_hw' prefix
        topology_type = topology_type[5:]

        # Cosmetics - adding underscores between capital letters
        return re.sub(r'(?<!^)(?=[A-Z])', '_', topology_type)

# def process_tech_drawing_json(tech_drawing_jsons_dir_path: str, part_name: str, topologies_dict: dict):
#     # Going over on all tech drawing jsons
#     for json_name in os.listdir(tech_drawing_jsons_dir_path):
#         # Processing only files that ends with .json
#         if part_name.endswith('.json'):
#             file_path = os.path.join(tech_drawing_jsons_dir_path, part_name)
#
#             # Read the JSON file
#             data = read_json(file_path)
#
#             """
#             I need to go over EACH TOPOLOGY:
#                 go over each HOLE GROUP:
#
#
#                     first, go over all HOLES, and assign them the following:
#                         assign for each hole the global tolerance: linear, and holes (4 attributes):
#                             - diam_tol_minus = hole_upper_general_tolerance
#                             - diam_tol_plus = hole_lower_general_tolerance
#                             - depth_tol_minus = linear_upper_general_tolerance
#                             - depth_tol_plus = linear_lower_general_tolerance
#                         assign material = material
#
#                     After finish going over the holes, check:
#                     if ALL 3 conditions are met:
#                     - drawing diameter +- diam_tol_plus == diameter
#                     - drawing depth +- depth_tol_plus == depth
#                     - quantity <= number of holes
#
#                         go over all HOLES:
#                             I check how many jobs there are for each hole.
#                             if there are holes with MORE JOBS than other holes:
#                                 assign the following to holes according to quantity (if quantity is 4, then assign to 4 holes)
#                                     - thread attributes (4 of them) if exists:
#                                         - has_thread = has_thread
#                                         - thread_nominal_dia_drawing = thread_nominal_diameter
#                                         - thread_pitch_drawing = thread_pitch
#                                         - thread_depth_drawing = thread_depth
#
#                                     - GD&T attributes (2 of them) if exists:
#                                         - tolerance_type = gdandt_type
#                                         - tolerance_value = gdandt_value
#
#
#             """


def process_tech_drawing_json(tech_drawing_jsons_dir_path: str, part_name: str, topologies_dict: dict):
    """
    Reads the technical drawing JSON and updates the Hole attributes in the topologies_dict.

    Matching Logic:
    1. Matches a Drawing Entry to a Hole Group via Diameter and Depth.
    2. Matches specific Holes within that Group via Quantity and Job Count (descending).
    """

    # 1. Construct file path and load data
    file_path = os.path.join(tech_drawing_jsons_dir_path, part_name)

    # Validation: Check if file exists
    if not os.path.exists(file_path):
        print(f"Warning: Technical drawing file not found at {file_path}")
        return

    tech_data = read_json(file_path)

    # Fill global fields
    hole_up_gen_tol = float(tech_data.get("hole_upper_general_tolerance"))
    hole_lower_gen_tol = float(tech_data.get("hole_lower_general_tolerance"))
    lin_up_gen_tol = float(tech_data.get("linear_upper_general_tolerance"))
    lin_lower_gen_tol = float(tech_data.get("linear_lower_general_tolerance"))
    material = str(tech_data.get("material"))

    ### Adding Global Attributes - Tolerances and Material ###
    # Go over all holes, and add the global attributes - tolerances and material
    for topology in topologies_dict.values():
        for hole_group in topology.holes_groups:
            for hole in hole_group.holes.values():
                hole.diam_tol_plus = hole_up_gen_tol
                hole.diam_tol_minus = hole_lower_gen_tol
                hole.depth_tol_plus = lin_up_gen_tol
                hole.depth_tol_minus = lin_lower_gen_tol
                hole.material = material

    # Defining the general tolerance to be the bigger of the two
    hole_gen_tol = hole_up_gen_tol if hole_up_gen_tol > abs(hole_lower_gen_tol) else abs(hole_lower_gen_tol)
    depth_gen_tol = lin_up_gen_tol if lin_up_gen_tol > abs(lin_lower_gen_tol) else abs(lin_lower_gen_tol)

    ### Adding Specific Attributes - Threads, and GD&T ###
    # Going over all hole callouts found in the technical drawing
    holes_callout = tech_data.get("holes_callout")
    for entry in holes_callout:
        try:
            # Parse drawing values (converting strings to appropriate types)
            drawing_quantity = int(entry.get("quantity"))
            drawing_diameter = float(entry.get("diameter"))
            drawing_depth = float(entry.get("depth"))
        except (ValueError, TypeError):
            print(f"Skipping invalid entry in {part_name}: {entry}")
            continue

        """
        We have two cases to deal with:
        1 - In "THRU" holes in the drawing, the depth is not given in the drawing, and it's set to 0 as default.
        2 - There are cases when part of a group has special attributes (such as GD&T) and the other part doesn't,
            so we look for hole groups in the CAM that has same or less than the quantity mentioned in the drawing.

        In order to deal with those two cases we define prioritization of the groups af follows:
        Priority 1: Exact Diameter, Exact Depth, Exact Quantity
        Priority 2: Exact Diameter, Exact Depth, less than Quantity
        Priority 3: Exact Diameter, Exact Quantity (in cases is THRU, depth is ignored)
        Priority 4: Exact Diameter, <= Quantity (depth is ignored)

        """
        # Lists to store valid candidates#
        # We separate them to enforce the "Exact Quantity" vs "Sufficient Quantity" priority
        exact_qty_candidates = []  # Stores best match where Group Size == Drawing Qty
        sufficient_qty_candidates = []  # Stores fallback match where Group Size > Drawing Qty

        # 3. Search ALL groups to find valid candidates
        for topology in topologies_dict.values():
            for hole_group in topology.holes_groups:

                # --- Geometric Filter ---

                # 1. Diameter Check (Always applies)
                delta_diameter = abs(drawing_diameter - hole_group.diameter)
                if delta_diameter > hole_gen_tol:
                    continue  # Skip this group when Diameter mismatch

                # 2. Depth Check (Conditional)
                # If drawing has depth (Priority 1 & 2 logic), we check tolerance.
                # If drawing depth is 0 (Priority 3 & 4 logic), we IGNORE depth check.
                if drawing_depth > 0:
                    delta_depth = abs(drawing_depth - hole_group.hole_depth)
                    if delta_depth > depth_gen_tol:
                        continue  # Skip: Depth mismatch when depth is required

                # If we reach here, the group is Geometrically Valid (Diameter + Depth/Ignored)
                # --- Quantity Prioritization ---
                group_size = len(hole_group.holes)
                if group_size == drawing_quantity:
                    exact_qty_candidates.append(hole_group)
                elif group_size > drawing_quantity:
                    sufficient_qty_candidates.append(hole_group)

        # 4. Selection Logic
        # This structure automatically satisfies our 4-tier priority:
        # - If depth > 0, we only have candidates that matched depth.
        # - If depth == 0, we have candidates where depth was ignored.
        # - In either case, we prefer Exact Quantity over Sufficient Quantity.
        target_group = None
        if exact_qty_candidates:
            target_group = exact_qty_candidates[0]
        elif sufficient_qty_candidates:
            target_group = sufficient_qty_candidates[0]

        # 5. Assign Attributes to the selected target group
        if target_group:

            # Sort holes by job count (Heuristic: complex holes have more jobs)
            current_holes = list(target_group.holes.values())
            current_holes.sort(key=lambda h: len(h.jobs), reverse=True)

            # Select the top N holes
            target_holes = current_holes[:drawing_quantity]

            for hole in target_holes:
                # Helper for mapping values
                def parse_float(val):
                    return float(val) if val is not None else 0.0

                # --- Tolerance Attributes ---
                # Statement is true only if a tolerance is specified in the hole callout
                if entry.get("drawing_tol_plus")>0 or entry.get("drawing_tol_minus")>0:
                    hole.diam_tol_plus = entry.get("drawing_tol_plus")
                    hole.diam_tol_minus = entry.get("drawing_tol_minus")

                # --- Thread Attributes ---
                if entry.get("has_thread") == 1:
                    hole.has_thread = 1
                    hole.thread_nominal_dia_drawing = parse_float(entry.get("thread_nominal_diameter"))
                    hole.thread_pitch_drawing = parse_float(entry.get("thread_pitch"))
                    hole.thread_depth_drawing = parse_float(entry.get("thread_depth"))
                    hole.thread_class_grade = str(entry.get("thread_class_grade"))

                # --- GD&T Attributes ---
                # Only assign if they are not None in the JSON
                if entry.get("gdandt_type") is not None:
                    hole.tolerance_type = entry.get("gdandt_type")
                    try:
                        hole.tolerance_value = float(entry.get("gdandt_value"))
                    except (ValueError, TypeError):
                        hole.tolerance_value = entry.get("gdandt_value")
        else:
            print(f"Warning: No match found for Dia={drawing_diameter}, Depth={drawing_depth}, Qty={drawing_quantity}")


        ######################




        # # Determine if we enforce depth checking - Priorities 3 & 4 apply only when drawing_depth==0
        # enforce_depth = drawing_depth > 0
        #
        # # --- Hole Groups Search Phase ---
        # target_group = None
        #
        # priorities = [1, 2] if drawing_depth > 0 else [3, 4]
        #
        # for priority in priorities:
        #     if target_group == None:
        #         target_group = find_best_match(drawing_quantity, drawing_diameter, drawing_depth,
        #                                        topologies_dict, tech_data, priority)
        #
        # for topology in topologies_dict.values():
        #     for hole_group in topology.holes_groups:
        #
        #         # Checking if Diameter matches
        #         delta_diameter = abs(drawing_diameter - hole_group.diameter)
        #         if delta_diameter >= hole_gen_tol:
        #             continue  # Diameter mismatch, skip group
        #
        #         # Check if Depth matches
        #         if drawing_depth > 0:
        #             delta_depth = abs(drawing_depth - hole_group.hole_depth)
        #             if delta_depth >= depth_gen_tol:
        #                 continue  # Depth mismatch, skip group
        #
        #         # --- Quantity Check & Sorting into the two candidates groups ---
        #         group_size = len(hole_group.holes)
        #         if group_size == drawing_quantity:
        #             # Priority 1 (with depth) or 3 (without depth)
        #             exact_matches.append(hole_group)
        #         elif group_size > drawing_quantity:
        #             # Priority 2 (with depth) or 4 (without depth)
        #             subset_matches.append(hole_group)
        #
        # ### --- Selecting the best candidate - the best matching group as stated earlier ---
        # target_group = None
        #
        # if exact_qty_matches:
        #     # Priority 1: Found a group with EXACT quantity
        #     target_group = exact_qty_matches[0]
        #     # (Optional: You could add logic here to handle if multiple exact matches exist)
        #
        # elif sufficient_qty_matches:
        #     # Priority 2: Fallback to a group with SUFFICIENT (more) holes
        #     target_group = sufficient_qty_matches[0]
        #
        # # 5. Apply Attributes to the selected target group
        # if target_group:
        #
        #     # HEURISTIC: Sort holes by number of jobs (Descending)
        #     current_holes = list(target_group.holes.values())
        #     current_holes.sort(key=lambda h: len(h.jobs), reverse=True)
        #
        #     # Select only the top N holes based on the drawing quantity
        #     target_holes = current_holes[:drawing_quantity]
        #
        #     for hole in target_holes:
        #
        #         # Helper for mapping values
        #         def parse_float(val):
        #             return float(val) if val is not None else 0.0
        #
        #         # --- Thread Attributes ---
        #         if entry.get("has_thread") == 1:
        #             hole.has_thread = 1
        #             hole.thread_nominal_dia_drawing = parse_float(entry.get("thread_nominal_diameter"))
        #             hole.thread_pitch_drawing = parse_float(entry.get("thread_pitch"))
        #             hole.thread_depth_drawing = parse_float(entry.get("thread_depth"))
        #             hole.thread_class_grade = str(entry.get("thread_class_grade"))
        #
        #         # --- GD&T Attributes ---
        #         if entry.get("gdandt_type") is not None:
        #             hole.tolerance_type = entry.get("gdandt_type")
        #             try:
        #                 hole.tolerance_value = float(entry.get("gdandt_value"))
        #             except (ValueError, TypeError):
        #                 hole.tolerance_value = entry.get("gdandt_value")
        # else:
        #     print(
        #         f"Warning: No matching hole group found for entry: Dia={drawing_diameter}, Depth={drawing_depth}, Qty={drawing_quantity}")
        #
        #     # Comparing if diameter, depth, and quantity fit
        #     if (delta_diameter <= hole_up_gen_tol
        #             and delta_depth <= lin_up_gen_tol
        #             and drawing_quantity <= len(hole_group.holes)):
        #
        #         # HEURISTIC: Sort holes by number of jobs (Descending)
        #         # We assume that holes with special properties (Thread, tight tolerance)
        #         # often have MORE operations performed on them.
        #         current_holes = list(hole_group.holes.values())
        #         current_holes.sort(key=lambda h: len(h.jobs), reverse=True)
        #
        #         # Select only the top N holes based on the drawing quantity
        #         target_holes = current_holes[:drawing_quantity]
        #
        #         # 4. Assign Attributes to the selected holes
        #         for hole in target_holes:
        #
        #             # Mapping tolerances as requested (Strings to Floats)
        #             # Note: Logic follows your specific mapping (Upper -> Minus, Lower -> Plus)
        #             def parse_float(val):
        #                 return float(val) if val is not None else 0.0
        #
        #             # --- Thread Attributes ---
        #             if entry.get("has_thread") == 1:
        #                 hole.has_thread = 1
        #                 hole.thread_nominal_dia_drawing = parse_float(entry.get("thread_nominal_diameter"))
        #                 hole.thread_pitch_drawing = parse_float(entry.get("thread_pitch"))
        #                 hole.thread_depth_drawing = parse_float(entry.get("thread_depth"))
        #                 hole.thread_class_grade = str(entry.get("thread_class_grade"))
        #
        #             # --- GD&T Attributes ---
        #             # Only assign if they are not None in the JSON
        #             if entry.get("gdandt_type") is not None:
        #                 hole.tolerance_type = entry.get("gdandt_type")
        #                 try:
        #                     hole.tolerance_value = float(entry.get("gdandt_value"))
        #                 except (ValueError, TypeError):
        #                     hole.tolerance_value = entry.get("gdandt_value")



# def process_tech_drawing_json(tech_drawing_jsons_dir_path: str, part_name: str, topologies_dict: dict):
#     """
#     Reads the technical drawing JSON and updates the Hole attributes in the topologies_dict.
#
#     Matching Logic:
#     1. Matches a Drawing Entry to a Hole Group via Diameter and Depth.
#     2. Matches specific Holes within that Group via Quantity and Job Count (descending).
#     """
#
#     # 1. Construct file path and load data
#     file_path = os.path.join(tech_drawing_jsons_dir_path, part_name)
#
#     # Validation: Check if file exists
#     if not os.path.exists(file_path):
#         print(f"Warning: Technical drawing file not found at {file_path}")
#         return
#
#     tech_data = read_json(file_path)
#
#     # Fill global fields
#     hole_up_gen_tol    = float(tech_data.get("hole_upper_general_tolerance"))
#     hole_lower_gen_tol = float(tech_data.get("hole_lower_general_tolerance"))
#     lin_up_gen_tol     = float(tech_data.get("linear_upper_general_tolerance"))
#     lin_lower_gen_tol  = float(tech_data.get("linear_lower_general_tolerance"))
#     material           = str(tech_data.get("material"))
#
#     ### Adding Global Attributes - Tolerances and Material ###
#     # Go over all holes, and add the global attributes - tolerances and material
#     for topology in topologies_dict.values():
#         for hole_group in topology.holes_groups:
#             for hole in hole_group.holes.values():
#                 hole.diam_tol_plus = hole_up_gen_tol
#                 hole.diam_tol_minus = hole_lower_gen_tol
#                 hole.depth_tol_plus = lin_up_gen_tol
#                 hole.depth_tol_minus = lin_lower_gen_tol
#                 hole.material = material
#
#     # Defining the general tolerance to be the bigger of the two
#     hole_gen_tol  = hole_up_gen_tol if hole_up_gen_tol>abs(hole_lower_gen_tol) else abs(hole_lower_gen_tol)
#     depth_gen_tol = lin_up_gen_tol if lin_up_gen_tol>abs(lin_lower_gen_tol) else abs(lin_lower_gen_tol)
#
#     ### Adding Specific Attributes - Threads, and GD&T ###
#     # Going over all hole callouts found in the technical drawing
#     holes_callout = tech_data.get("holes_callout")
#     for entry in holes_callout:
#         try:
#             # Parse drawing values (converting strings to appropriate types)
#             drawing_quantity = float(entry.get("quantity"))
#             drawing_diameter = float(entry.get("diameter"))
#             drawing_depth    = float(entry.get("depth"))
#         except (ValueError, TypeError):
#             print(f"Skipping invalid entry in {part_name}: {entry}")
#             continue
#
#         # Lists to store candidate groups based on priority
#         exact_qty_matches = []  # Priority 1: Group Size == Drawing Quantity
#         sufficient_qty_matches = []  # Priority 2: Group Size > Drawing Quantity
#
#         """
#         We have two cases to deal with:
#         1 - In "THRU" holes in the drawing, the depth is not given in the drawing, and it's set to 0 as default.
#         2 - There are cases when part of a group has special attributes (such as GD&T) and the other part doesn't,
#             so we look for hole groups in the CAM that has same or less than the quantity mentioned in the drawing.
#
#         In order to deal with those two cases we define prioritization of the groups af follows:
#         Priority 1: Exact Diameter, Exact Quantity, Exact Depth
#         Priority 2: Exact Diameter, <= Quantity, Exact Depth
#         Priority 3: Exact Diameter, Exact Quantity (in cases is THRU, depth is ignored)
#         Priority 4: Exact Diameter, <= Quantity (depth is ignored)
#
#         """
#         # Initialize candidates for this specific drawing entry
#         exact_qty_match = None       # Stores best match where Group Size == Drawing Qty
#         sufficient_qty_match = None  # Stores fallback match where Group Size > Drawing Qty
#
#         # Determine if we enforce depth checking - Priorities 3 & 4 apply only when drawing_depth==0
#         enforce_depth = drawing_depth > 0
#
#         # --- Hole Groups Search Phase ---
#         target_group = None
#
#         priorities = [1,2] if drawing_depth>0 else [3,4]
#
#
#         for priority in priorities:
#             if target_group==None:
#                 target_group = find_best_match(drawing_quantity, drawing_diameter, drawing_depth,
#                                                topologies_dict, tech_data, priority)
#
#         for topology in topologies_dict.values():
#             for hole_group in topology.holes_groups:
#
#                 # Checking if Diameter matches
#                 delta_diameter = abs(drawing_diameter - hole_group.diameter)
#                 if delta_diameter >= hole_gen_tol:
#                     continue # Diameter mismatch, skip group
#
#                 # Check if Depth matches
#                 if drawing_depth > 0:
#                     delta_depth = abs(drawing_depth - hole_group.hole_depth)
#                     if delta_depth >= depth_gen_tol:
#                         continue  # Depth mismatch, skip group
#
#
#                 # --- Quantity Check & Sorting into the two candidates groups ---
#                 group_size = len(hole_group.holes)
#                 if group_size == drawing_quantity:
#                     # Priority 1 (with depth) or 3 (without depth)
#                     exact_matches.append(hole_group)
#                 elif group_size > drawing_quantity:
#                     # Priority 2 (with depth) or 4 (without depth)
#                     subset_matches.append(hole_group)
#
#         ### --- Selecting the best candidate - the best matching group as stated earlier ---
#         target_group = None
#
#         if exact_qty_matches:
#             # Priority 1: Found a group with EXACT quantity
#             target_group = exact_qty_matches[0]
#             # (Optional: You could add logic here to handle if multiple exact matches exist)
#
#         elif sufficient_qty_matches:
#             # Priority 2: Fallback to a group with SUFFICIENT (more) holes
#             target_group = sufficient_qty_matches[0]
#
#         # 5. Apply Attributes to the selected target group
#         if target_group:
#
#             # HEURISTIC: Sort holes by number of jobs (Descending)
#             current_holes = list(target_group.holes.values())
#             current_holes.sort(key=lambda h: len(h.jobs), reverse=True)
#
#             # Select only the top N holes based on the drawing quantity
#             target_holes = current_holes[:drawing_quantity]
#
#             for hole in target_holes:
#
#                 # Helper for mapping values
#                 def parse_float(val):
#                     return float(val) if val is not None else 0.0
#
#                 # --- Thread Attributes ---
#                 if entry.get("has_thread") == 1:
#                     hole.has_thread = 1
#                     hole.thread_nominal_dia_drawing = parse_float(entry.get("thread_nominal_diameter"))
#                     hole.thread_pitch_drawing = parse_float(entry.get("thread_pitch"))
#                     hole.thread_depth_drawing = parse_float(entry.get("thread_depth"))
#                     hole.thread_class_grade = str(entry.get("thread_class_grade"))
#
#                 # --- GD&T Attributes ---
#                 if entry.get("gdandt_type") is not None:
#                     hole.tolerance_type = entry.get("gdandt_type")
#                     try:
#                         hole.tolerance_value = float(entry.get("gdandt_value"))
#                     except (ValueError, TypeError):
#                         hole.tolerance_value = entry.get("gdandt_value")
#         else:
#             print(
#                 f"Warning: No matching hole group found for entry: Dia={drawing_diameter}, Depth={drawing_depth}, Qty={drawing_quantity}")
#
#
#
#
#
#
#
#                 # Comparing if diameter, depth, and quantity fit
#                 if (delta_diameter <= hole_up_gen_tol
#                     and delta_depth <= lin_up_gen_tol
#                     and drawing_quantity <= len(hole_group.holes)):
#
#                     # HEURISTIC: Sort holes by number of jobs (Descending)
#                     # We assume that holes with special properties (Thread, tight tolerance)
#                     # often have MORE operations performed on them.
#                     current_holes = list(hole_group.holes.values())
#                     current_holes.sort(key=lambda h: len(h.jobs), reverse=True)
#
#                     # Select only the top N holes based on the drawing quantity
#                     target_holes = current_holes[:drawing_quantity]
#
#                     # 4. Assign Attributes to the selected holes
#                     for hole in target_holes:
#
#                         # Mapping tolerances as requested (Strings to Floats)
#                         # Note: Logic follows your specific mapping (Upper -> Minus, Lower -> Plus)
#                         def parse_float(val):
#                             return float(val) if val is not None else 0.0
#
#                         # --- Thread Attributes ---
#                         if entry.get("has_thread") == 1:
#                             hole.has_thread = 1
#                             hole.thread_nominal_dia_drawing = parse_float(entry.get("thread_nominal_diameter"))
#                             hole.thread_pitch_drawing       = parse_float(entry.get("thread_pitch"))
#                             hole.thread_depth_drawing       = parse_float(entry.get("thread_depth"))
#                             hole.thread_class_grade         = str(entry.get("thread_class_grade"))
#
#                         # --- GD&T Attributes ---
#                         # Only assign if they are not None in the JSON
#                         if entry.get("gdandt_type") is not None:
#                             hole.tolerance_type = entry.get("gdandt_type")
#                             try:
#                                 hole.tolerance_value = float(entry.get("gdandt_value"))
#                             except (ValueError, TypeError):
#                                 hole.tolerance_value = entry.get("gdandt_value")




# def compute_segment_len(geom_shape) -> float:
#     a = abs(geom_shape["p0"][0] - geom_shape["p1"][0])
#     b = abs(geom_shape["p0"][1] - geom_shape["p1"][1])
#     return math.sqrt(math.pow(a, 2) + math.pow(b, 2))


# def mask_segments_compute(mask_str):
#     """ A function for one-hot-encoding a topology mask """
#     # Reverse to assign seg1 = first digit, seg2 = second, etc.
#     digits = [int(d) for d in mask_str]
#
#     # Helper: convert a single digit (1–4) to 4-bit one-hot
#     def to_vec(d):
#         vec = [0, 0, 0, 0]
#         if 1 <= d <= 4:
#             vec[d - 1] = 1
#         return vec
#
#     # Initialize all segments to zeros
#     segs = [[0, 0, 0, 0] for _ in range(6)]
#
#     # Fill according to digits
#     for i, d in enumerate(digits):
#         if i < 6:
#             segs[i] = to_vec(d)
#
#     return segs

# class Mask(Enum):
#     """
#     This class is used to deal with JSON's field '_geomShapeMask' - this field
#     holds a vector of numbers that defines the topology of a hole, but not the
#     hole's dimensions. The humber are written Right to Left (as in Hebrew).
#     Each number in the mask tells us the shape of the segments composing the hole.
#     """
#
#     PLANE = 1
#     CYLINDER = 2
#     CONIC = 3
#     CHAMFER = 4
#
#     # I can access the strings by using: "Mask(number 1-4).name"


def validate_job(job, part_name):
    """
    This function purpose is for verifying that all the JSON fields that are being used are either:
    1 - Existing
    2 - Not None
    3 - Bigger than 0
    If any mistakes are found, it prints information about them

    *Note - the order of the fields on this code are similar to the order of the fields on the JSON

    Args:
        job (dict): Holds all the fields of the job
        part_name (str): The name of the part
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
        if job_type in ["NC_PROFILE", "NC_CHAMFER"]:
            geometry = job["geometry"]
            if geometry.get("poly_arcs") is None or len(geometry.get("poly_arcs"))==0:   # Checking poly_arcs field
                errors.append("geometry.poly_arcs field is invalid")
            if job.get("operation_parameters") is None:                        # Checking operation_parameters field
                errors.append("operation_parameters field is invalid")
            elif "Unsupported type" in job.get("operation_parameters").values(): # Checking if there is a value with "Unsupported type"
                errors.append("Unsupported type found in operation_parameters")

        if job["geometry"].get("recognized_holes_groups") is None:                        # Checking recognized_holes_groups field
            if job_type in drilling_types:
                errors.append("recognized_holes_groups field is invalid OR it's a pre-drilling operation")
            if job_type in non_drilling_types:
                errors.append("recognized_holes_groups field is invalid OR this operation isn't performed on holes")

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

                # True if it's a Thread Milling Job
                elif job_type == "NC_THREAD":
                    if job.get("thread_mill") is None or len(job.get("thread_mill")) == 0:
                        errors.append("thread_mill field is invalid")

                    # # Checking again the thread fields, but also checking if their value is not zero
                    # # Note - the next 'for loop' will result in error if one of the fields are zero
                    # fields_not_none = ["_geom_thread_depth", "_geom_thread_diameter", "_geom_thread_pitch"]
                    # for field in fields_not_none:
                    #     if holes_group_info.get(field) is None or holes_group_info.get(field) == 0:
                    #         errors.append(f"{field} field is invalid")

    # Printing the errors if there are any
    if errors:
        # print("\n")
        print(f"Job name: {job['name']} | Job type: {job['type']} | Job number: ({job["job_number"]}) | Part name:{part_name}")
        for error in errors:
            print(error)
        print("\n")





# def find_best_match(drawing_quantity, drawing_diameter, drawing_depth,
#                     topologies_dict, tech_data, priority, hole_gen_tol, depth_gen_tol):
#
#
#     if priority in [1,2]:   # Exact Diameter, Exact Depth, Exact Quantity
#
#         # going over on all hole groups
#         for topology in topologies_dict.values():
#             for hole_group in topology.holes_groups:
#
#                 # Comparing if diameter, depth, and quantity fit
#                 if delta_diameter <= hole_gen_tol and delta_depth <= depth_gen_tol:
#
#                     if drawing_quantity == len(hole_group.holes)
#
#
#     # elif priority == 2: # Exact Diameter, <= Quantity, Exact Depth
#     #
#     # elif priority == 3: # Exact Diameter, Exact Quantity (in cases of THRU holes, depth is ignored)
#     #
#     # elif priority == 4: # Exact Diameter, <= Quantity (in cases of THRU holes, depth is ignored)
#
#     return 1



