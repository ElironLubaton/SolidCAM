from MACs_Conversions import compare_coordinates, compare_geometries
from Utilities_and_Cosmetics import process_job_name, process_tool_type_name
import math

# Global Variables
drilling_types = ["NC_DRILL_OLD", "NC_DRILL_DEEP", "NC_THREAD", "NC_DRILL_HR", "NC_JOB_MW_DRILL_5X"]
non_drilling_types = ["NC_PROFILE", "NC_CHAMFER"]

bold_s = '\033[1m' # Start to write in bold
bold_e = '\033[0m' # End to write in bold


class Topology:
  """ An object of this class holds all the holes in the specified topology."""
  def __init__(self, topology_type, topology_mask):
    """ topology_mask - 1:Plane,  2:Cylinder,  3:Conic,  4:Chamfer """
    self.topology = topology_type           # String containing topology's name (e.g, CounterBore)
    self.topology_mask = topology_mask # Int containing topology's mask
    self.holes_groups = []             # The hole groups that belong to this topology
    self.jobs_orders_dict = dict()     # Used for printing the legend in plots

  def add_hole_group(self, job, new_coordinates, holes_group_info, part_name):
    """
    This method creates a new hole group ONLY if the geometric shape of the hole group is new.
    If the geometric shape is not new, we just update the number of the instances
    in the hole group.

    Returns:
      group: HoleGroup instance - existing one, or a new one
    """
    new_geom_shape = holes_group_info["_geom_ShapePoly"]
    new_job = None

    # Going over on all existing hole groups and check if the "new" geometry shape already exists
    for existing_group in self.holes_groups:
      # If true, then geometry shape or its reverse already exists, so just updating number of centers
      if compare_geometries(new_geom_shape, existing_group.geom_shape):
        # Going over the centers in the new coordinates in order to update centers
        for new_center in new_coordinates:
          # Going over all the jobs inside the hole group
          for existing_job in existing_group.jobs:
            # Add the new center if he is really new, or he already exists inside the hole group
            not_exist_flag, existing_center = compare_coordinates(new_center, set(existing_job.holes.keys()),
                                                     existing_group.hole_depth,job["home_number"],
                                                     existing_job.parallel_home_numbers)
            # If true, the new_center doesn't exist
            if not_exist_flag:
              new_hole = Hole(new_center)                       # Creating a new Hole instance
              new_job = new_hole.add_job(job, holes_group_info) # Assigning the job to the new Hole instance
              existing_group.holes[new_center] = new_hole       # Adding the new Hole instance to the existing holes group
              new_job.centers.add(new_center)                   # Adding the new_center to the job's centers
              existing_group.centers.add(new_center)            # Adding the new_center to the existing holes group centers
            else: # The center already exists
              existing_group.holes[existing_center].add_job(job, holes_group_info)

            # if compare_coordinates(new_center, list(existing_job.holes.keys()), existing_group.hole_depth,
            #                        job["home_number"], existing_job.parallel_home_numbers):
            #   existing_group.centers.add(new_center)
            #   # Creating a new Hole instance
            #   new_hole = Hole(new_center)
            #   # Assigning the job to the new hole
            #   new_job = new_hole.add_job(job, holes_group_info)
            #   # Adding the new hole to the existing hole group
            #   existing_group.holes[new_center] = new_hole  # Adding the new_hole to the new_holes_group

        # returning the updated existing group
        return existing_group


    # The geometry shape doesn't exist
    # Creating a new instance of HoleGroup
    new_group = HoleGroup(new_coordinates, new_geom_shape, holes_group_info, part_name)

    # For each hole we create a new Hole instance
    for new_center in new_coordinates:
      new_hole = Hole(new_center)                       # Creating a new Hole instance
      new_job = new_hole.add_job(job, holes_group_info) # Assigning the job to the new hole
      new_group.holes[new_center] = new_hole            # Adding the new_hole to the new_holes_group

    # Adding the new job to the new group
    new_group.jobs.append(new_job)
    # Adding the new hole group to the Topology
    self.holes_groups.append(new_group)


  def update_jobs_orders_dict(self):
    """
    This method updates the dictionary that holds all the jobs orders of all holes groups.
    It is used only for statistics purposes
    """
    for hole_group in self.holes_groups:
      if hole_group.jobs_order not in self.jobs_orders_dict:
        self.jobs_orders_dict[hole_group.jobs_order] = 'Order ' + str(len(self.jobs_orders_dict)+1)



class HoleGroup:
  """
  An object of this class holds all the holes in the same hole group, and the
  description of the hole.

  *Note: 'self.jobs' field holds all the jobs done on the holes that belong to that hole group,
          but NOT all jobs necessarily were performed on all the holes (E.g, a hole that has a lower tolerance,
          so it has one more job performed on it).
  """
  def __init__(self, new_coordinates, geom_shape, holes_group_info, part_name):
    self.holes = {}                      # A dict that holds all the holes in that hole group
    self.centers = set(new_coordinates)  # The (x,y) coordinates of holes in this hole group
    self.jobs = []                       # All the jobs performed on this hole group
    self.jobs_order = ''               # A string that holds the order of the jobs
    self.geom_shape = geom_shape         # Geomertric shape of the holes in this hole group
    self.part_name            = part_name
    self.diameter             = abs(2*min(item["p0"][0] for item in geom_shape)) # The smallest diameter of the holes
    self.hole_depth           = holes_group_info["_geom_depth"]                  # Hole's depth
    self.thread_depth         = holes_group_info["_geom_thread_depth"]           # Hole's thread depth
    self.thread_hole_diameter = holes_group_info["_geom_thread_hole_diameter"]   # Hole's thread diameter
    self.thread_pitch         = holes_group_info["_geom_thread_pitch"]           # Hole's thread pitch
    self.fastener_size        = holes_group_info["_fastener_size"]
    self.standard             = holes_group_info["_standard"]


  # def add_job(self, job, new_coordinates, holes_group_info):
  #   """
  #   This method assigns a job to a hole group ONLY if the same exact job doesn't
  #   already exist - we check for existence via comparison of job depth, job type,
  #   tool type, and tool parameters.
  #   """
  #
  #   tool_type = process_tool_type_name(job['tool']['tool_type']) # Cosmetics
  #   job_depth = job['job_depth']
  #   job_type = job['type']
  #   tool_parameters = job['tool']
  #   if "ver" in tool_parameters:     # Removing unnecessary field from json: "ver" under tool_parameters
  #     tool_parameters.pop("ver")
  #
  #   # Note - In Multi-Axis Drilling jobs, the job depth will be defined by the tech_depth inside the hole group info
  #   if job["type"] == "NC_JOB_MW_DRILL_5X":
  #     job_depth = holes_group_info["_tech_depth"]
  #
  #   # Checking if the job already exists - Going over all the existing jobs in that hole group
  #   for existing_job in self.jobs:
  #     # if true, then job already exists, so existing the function
  #     if (existing_job.job_depth       == job_depth and      # Same job depth
  #         existing_job.job_type        == job_type  and      # Same job type
  #         existing_job.tool_type       == tool_type and      # Same tool type
  #         existing_job.tool_parameters == tool_parameters):  # Same tool parameters
  #       return
  #
  #   # If got here, then the job is new
  #   new_job = Job(job, tool_type, new_coordinates, holes_group_info)
  #   self.jobs.append(new_job)
  #   self.jobs_order += f"{new_job.job_type} - {new_job.tool_type} | "


  def add_tolerance(self, tolerance_type, upper_tolerance, lower_tolerance):
    """ Adding tolerances for each hole according to the EXCEL files from Doron """
    for hole in self.holes:
      hole.tolerance = tolerance_type
      hole.upper_tolerance = upper_tolerance
      hole.lower_tolerance = lower_tolerance


  def print(self):
    """ This method prints selected fields from that hole group """
    print(f"Part name: {self.part_name}")
    print(f"Number of instances : {len(self.centers)}")
    print(f"Geometry shape: {self.geom_shape}") # Print when checking MACs
    print(f"Holes centers: {{{', '.join(f'({x}, {y}, {z})' for x, y, z in self.centers)}}}")  # For debugging
    print(f"Diameter: {self.diameter}")
    print(f"Depth: {round(self.hole_depth, 3)}")

    print(f"\nEach hole, and the jobs performed on it:")
    for _, hole in self.holes.items():
    # for hole in self.holes:
      print(f"Hole position at {tuple(float(x) for x in hole.position)}")
      print(f"Hole tolerance type: {hole.tolerance_type}, upper: {hole.upper_tolerance}, lower: {hole.lower_tolerance}")
      for i, job in enumerate(hole.jobs):
        print(f"{i + 1} - {job}")
      print('')

    # print(f"{bold_s}{len(self.jobs)} jobs total{bold_e} were performed on this hole group.\nThe order they're being exectued:")
    # for i, job in enumerate(self.jobs):
    #   print(f"{i+1} - {job}")
    # print('')



class Hole:
  """
  An object of this class holds a hole - it's position, tolerance, and jobs performed on it.
  """
  def __init__(self, new_coordinates):
    self.position = new_coordinates
    self.tolerance_type = None
    self.upper_tolerance = None
    self.lower_tolerance = None
    self.jobs = []                   # The jobs performed on this hole by the order they were performed

  def add_job(self, job, holes_group_info):
    """ This method assigns a job to a hole """

    tool_type = process_tool_type_name(job['tool']['tool_type'])  # Cosmetics

    new_job = Job(job, tool_type, holes_group_info)   # Creating a new Job instance
    new_job.centers.add(self.position)                # Updating the set of centers
    new_job.holes[self.position] = self               # Updating the holes dictionary
    self.jobs.append(new_job)                         # Adding the job

    return new_job



class Job:
  """
  An object of this class holds a job that is done on a hole.
  Each field holds the json's field with the same name.
  """
  def __init__(self, job, tool_type, holes_group_info):
    self.centers = set()                        # The (x,y) coordinates of holes that are being worked by this job
    self.holes = {}
    self.job_number = job["job_number"]           # Job's index in SolidCAM
    self.job_name = job['name']                   # Job name as defined by the user
    self.job_type = job['type']                   # Technology used (e.g, 2_5D_Drilling)
    self.tool_type = tool_type                    # Tool being used (e.g, End Mill)
    self.tool_parameters = job['tool']            # Tool parameters
    self.job_depth = job['job_depth']             # How deep the tool goes in, NOT taking into account the tool's tip
    self.tool_depth = None                        # How deep the tool goes in, taking into account the tool's tip
    self.thread_mill_params = job["thread_mill"]  # Thread Milling parameters - not None only on this job
    self.op_params = job["operation_parameters"]  # Profile & Chamfer parameters - not None only on this jobs

    self.home_number = job['home_number']
    self.parallel_home_numbers = job['home_vParallelHomeNumbers']

    # Assign drill-related attributes depending on job type on the bottom functions
    self.drill_cycle_type =     None
    self.drill_gcode_name =     None
    self.drill_params =         None
    self.cycle_is_using =       None
    self.deep_drill_segments =  None  # Multi-depth Drilling parameters - not None only on Multi-depth Drilling jobs.
    self.depth_diameter_value = None  # To which diameter of the head the tool gets inside the material
    self.depth_type =           None  # Either Cutter tip, Full diameter, Diameter value
    self.decide_drill_params(job, holes_group_info) # Assign drill-related attributes depending on job type
    self.compute_tool_depth()  # How deep the tool goes in, taking into account the tool's tip


  def __repr__(self):
    # return 'Job type & Tool type: {}, Job name: {}'.format(f"{self.job_type} - {self.tool_type}", self.job_name)
    return 'Job type: {} | Tool type: {} | Job name and number: {} ({})'.format(self.job_type, self.tool_type, self.job_name, self.job_number)


  # todo need to change this function so it would stop refering drilling and non-drilling separately
  def decide_drill_params(self, job, holes_group_info):
    """
    This method decides the drill parameters for the job, depending on the job type.
    """

    # True if it's NOT a drilling job, so no drill parameters to save
    if self.job_type not in drilling_types:
      return
    # True if it's a drilling job
    else:
      drill = job.get("drill", {})
      cycle = drill.get("cycle", {})

      # Defining the parameters that all drilling jobs contain
      self.drill_cycle_type = cycle.get("drill_type")
      self.drill_gcode_name = cycle.get("gcode_name")
      self.drill_params = cycle.get("params")
      self.cycle_is_using = drill.get("cycle_isUsing")

      # True if it's Multi-Axis Drilling job
      if self.job_type == "NC_JOB_MW_DRILL_5X":
        # Saving the depth diameter value
        self.depth_diameter_value = holes_group_info["_tech_depth_type_val"]
        # Deciding the depth type
        depth_type = holes_group_info["_tech_depth_type"]
        if depth_type == "DrMCT_CutterTip":
          self.depth_type = "Cutter_Tip"
        elif depth_type == "DrMCT_DiaFull":
          self.depth_type = "Full_Diameter"
        elif depth_type == "DrMCT_DiaValue":
          self.depth_type = "Diameter_value"

      # True if it's a Drilling job, but NOT Multi-Axis Drilling
      else:
        # Saving the depth diameter value
        self.depth_diameter_value = drill.get("depth_diameter_value")
        # Deciding the depth type
        if drill["depth_is_cutter_tip"]:
          self.depth_type = "Cutter_Tip"
        elif drill["depth_is_full_diameter"]:
          self.depth_type = "Full_Diameter"
        elif drill["depth_is_tool_Diameter"]:
          self.depth_type = "Tool_Diameter"

        # True if it's Multi-Depth Drilling job
        if self.job_type == "NC_DRILL_DEEP":
          self.deep_drill_segments = drill.get("deepDrillSegments")




  def compute_tool_depth(self):
    """
    This method computes the tool depth based on the tool's head angle, and the depth diameter value.
    tool depth takes into account how deep the tool's tip goes inside the material.
    It deals with 3 different cases:
    1 - Drilling jobs, not including Multi-Axis Drilling jobs.
    2 - Multi Axis Drilling jobs.
    3 - Profile and Chamfer jobs.

    The computation goes as follows:
    tool depth = job depth + tip depth
    """

    # Saving the tool's head angle
    tool_angle = self.tool_parameters["parameters"][0]["value"]
    tool_depth = 0

    # True if the job is one of the drilling jobs
    if self.job_type in drilling_types:
      tip_depth = self.depth_diameter_value / math.tan(math.radians(tool_angle))
      tool_depth = self.job_depth + tip_depth

    # todo Need to update this part once I have recognized hole groups in Profile and Chamfer jobs
    # todo It is crucial to update it because the tool Ball Nose doesn't have a flat head
    # True if the job in Profile or Chamfer
    elif self.job_type == ["NC_PROFILE"] or self.job_type == ["NC_CHAMFER"]:
      tool_depth = self.job_depth

    return tool_depth



