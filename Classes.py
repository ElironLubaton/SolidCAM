from MACs_Conversions import compare_coordinates, compare_geometries
from Utilities_and_Cosmetics import process_job_name, process_tool_type_name, remove_non_ascii, mask_segments_compute
import math



# Global variables - defines which jobs are of intrest
drilling_types = ["NC_DRILL_OLD", "NC_DRILL_DEEP", "NC_THREAD", "NC_DRILL_HR", "NC_JOB_MW_DRILL_5X"]
non_drilling_types = ["NC_PROFILE", "NC_CHAMFER", "NC_JOB_HSS_PARALLEL_TO_CURVE"]

bold_s = '\033[1m' # Start to write in bold
bold_e = '\033[0m' # End to write in bold


class Topology:
  """ An object of this class holds all the holes in the specified topology."""
  def __init__(self, topology_type, topology_mask):
    """ topology_mask - 1:Plane,  2:Cylinder,  3:Conic,  4:Chamfer """
    self.topology_mask = topology_mask  # Int containing topology's mask
    self.topology = topology_type       # String containing topology's name (e.g, CounterBore)
    self.holes_groups = []              # The hole groups that belong to this topology
    self.jobs_orders_dict = dict()      # Used for printing the legend in plots

  def add_hole_group(self,job, new_coordinates, holes_group_info, part_name):
    """
    This method does the following:
    1 - Creates HoleGroup instance - only in the geometric shape (geom_ShapePoly field in JSON) doesn't exist in that topology.
    2 - Creates a Hole instance - only if the hole doesn't exist in that hole group).

    Args:
      job (dict): Holds all information about the job.
      new_coordinates (set): Holds a 3-tuples with the (x,y,z) coordinates of each hole
      holes_group_info (dict): Holds all information about the hole group being processed
      part_name (str): Holds the part name defined by the user
    """

    new_geom_shape = holes_group_info["_geom_ShapePoly"]
    job_number = job["job_number"]
    new_group_flag = True

    # Going over on all existing hole groups and check if the "new" geometry shape already exists
    for existing_group in self.holes_groups:
      # If true, then geometry shape or its reverse already exists, so just updating number of centers
      if compare_geometries(new_geom_shape, existing_group.geom_shape, job_number):
        new_group_flag = False
        # Going over the centers in the new coordinates in order to update centers
        for new_center_coordinates in new_coordinates:
          # Add the new center if he is really new, or he already exists inside the hole group
          hole_exist_flag, hole_instance = compare_coordinates(new_center_coordinates, existing_group,
                                                          job["home_number"], existing_group.hole_depth,
                                                          job_number)
          # If True, the Hole object already exists - just add the job to that existing Hole instance
          if hole_exist_flag:
            hole_instance.add_job(job,holes_group_info)
          # If False, the hole object does NOT exist - creating a new Hole object, and adding the job
          else:
            existing_group.add_hole(job, holes_group_info, new_center_coordinates)

    # If true, then the hole group is new (the geometry shape doesn't exist)
    if new_group_flag:
      # Creating a new instance of HoleGroup
      new_group = HoleGroup(new_geom_shape, holes_group_info, part_name, self)

      # For each hole we create a new Hole instance, and add it to the new hole group
      for new_center_coordinates in new_coordinates:
        new_group.add_hole(job, holes_group_info, new_center_coordinates)

      # Adding the new hole group to the Topology
      self.holes_groups.append(new_group)


  # def update_jobs_orders_dict(self):
  #   """
  #   This method updates the dictionary that holds all the jobs orders of all holes groups.
  #   It is used only for statistics purposes
  #   """
  #   for hole_group in self.holes_groups:
  #     if hole_group.jobs_order not in self.jobs_orders_dict:
  #       self.jobs_orders_dict[hole_group.jobs_order] = 'Order ' + str(len(self.jobs_orders_dict)+1)


class HoleGroup:
  """
  An object of this class holds all the holes in the same hole group, and the
  description of the hole.

  *Note: 'self.jobs' field holds all the jobs done on the holes that belong to that hole group,
          but NOT all jobs necessarily were performed on all the holes (E.g, a hole that has a lower tolerance,
          so it has one more job performed on it).
  """
  def __init__(self, geom_shape, holes_group_info, part_name, parent_topology):
    self.holes = {}                              # dict: holds all the holes in that hole group - key is hole coordinates
    self.centers = set()                         # set:  holds the (x,y,z) coordinates of holes in this hole group
    # self.jobs = []                             # list: holds all the jobs performed on this hole group
    # self.jobs_order = ''                       # str:  holds the order of the jobs
    self.geom_shape = geom_shape                 # list: holds dicts which specifies the geometric shape of the holes in this hole group
    self.parent_topology      = parent_topology  # Topology: a pointer to the parent topology
    self.part_name            = part_name        # str: the part's name
    self.diameter             = abs(2*min(item["p0"][0] for item in geom_shape)) # The smallest diameter of the holes
    self.hole_depth           = holes_group_info["_geom_depth"]                  # Hole's depth

    # todo I think I need to move this attribute to Hole class - It can also be infered
    self.fastener_size        = remove_non_ascii(holes_group_info["_fastener_size"])


  def add_hole(self, job, holes_group_info, new_center_coordinates):
    """
    This method does the following:
    1 - Creates a new Hole instance, and assign the job to it
    2 - Adds the new Hole instance to the holes group.

    Args:
      job (dict): Holds all information about the job.
      holes_group_info (dict): Holds all information about the hole group being processed
      new_center_coordinates(3-tuple): Holds the (x,y,z) coordinates of this hole
    """
    # Creating a new Hole instance
    new_hole = Hole(new_center_coordinates, job, self)
    # Assigning the job to the new hole
    new_hole.add_job(job, holes_group_info)
    # Adding the new_hole to the group
    self.holes[new_center_coordinates] = new_hole
    # Adding the new coordinates to the group
    self.centers.add(new_center_coordinates)


  # def add_xls_info(self, tolerance_type, upper_tolerance, lower_tolerance, material,
  #                  thread_nominal_diameter, thread_pitch, thread_tolerance_class, is_thread_thru):
  #   """ Adding material and tolerances for each hole according to the EXCEL files from Doron """
  #   self.material = material
  #   for hole in self.holes:
  #     hole.tolerance = tolerance_type
  #     hole.upper_tolerance = upper_tolerance
  #     hole.lower_tolerance = lower_tolerance
  #
  #     hole.thread_nominal_diameter = thread_nominal_diameter
  #     hole.thread_pitch = thread_pitch
  #     hole.thread_tolerance_class = thread_tolerance_class
  #     hole.is_thread_thru = is_thread_thru


  def print(self, group_index):
    """ This method prints selected fields from that hole group """
    # print(f"Part name: {self.part_name}")
    print(f"Number of instances in Hole Group {group_index}:  {len(self.centers)}")
    print(f"Geometry shape: {self.geom_shape}") # Print when checking MACs
    print(f"Holes centers: {{{', '.join(f'({x}, {y}, {z})' for x, y, z in self.centers)}}}")  # DEBUGGING
    print(f"Diameter: {self.diameter} | Depth: {round(self.hole_depth, 3)}")
    # print(f"Depth: {round(self.hole_depth, 3)}")

    print(f"\nEach hole, and the jobs performed on it:")
    for hole in self.holes.values():
      print(f"Hole position at {tuple(float(x) for x in hole.center_coordinates)}")
      # print(f"Hole tolerance type: {hole.tolerance_type} | upper: {hole.upper_tolerance} | lower: {hole.lower_tolerance}") # DEBUGGING
      # print(f"thread_nominal_diameter: {hole.thread_nominal_diameter} | thread_pitch: {hole.thread_pitch} " # DEBUGGING
      #       f"| standard: {hole.standard} | thread_depth: {hole.thread_depth}")                             # DEBUGGING
      for i, job in enumerate(hole.jobs):
        print(f"{i + 1} - {job}")
      print("________________________________________________")
    print("                NEW HOLE GROUP                 ")
    print("*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-")


## Hole class for when I'm going to create a database for my ML model
# class Hole:
#   """
#   An object of this class holds a hole - it's position, tolerance, and jobs performed on it.
#   """
#   def __init__(self, new_coordinates, job, parent_hole_group):
#     # The next few blocks of parameters are for INTERNAL use
#     self.parent_hole_group = parent_hole_group  # pointer to the hole group which this hole belongs to
#     self.center_coordinates = new_coordinates
#     self.jobs = []  # The jobs performed on this hole by the order they were performed
#     self.tolerance_type = None
#     self.upper_tolerance = None
#     self.lower_tolerance = None
#
#     # Threading attributes deducted from tool parameters
#     self.thread_nominal_diameter.diameter = None   # float: Nominal diameter (in mm) of the thread, e.g., 8 for an M8 thread.
#     self.thread_pitch = None              # float: Thread pitch (in mm). E.g., 1.25 for M8x1.25
#     self.standard = None                  # str:   The thread's standard
#     self.thread_depth = None              # float: The depth of the thread
#
#     # todo I don't know YET how to compute the field below - data from the techinical drawing is needed
#     self.thread_tolerance_class = None  # str:   Thread tolerance class, defining the tolerance and fit for the thread. E.g., 6H.
#
#     ###################################################
#     # Those parameters are for machine learning use
#     # Before doing all the fields below, I need to ask Eran (or Tatyana) for some of the fields
#     self.is_thru = None         # 0/1 - Eran/Tatyana # todo
#     self.main_diameter = None   # in mm - nominal bore before any thread - JSON
#     self.hole_depth = None      # in mm - for blind, if THRU, set to wall thickness or NaN - JSON
#     self.mask_seg1 = self.mask_seg2 = self.mask_seg3 = None # binary mask - 4 values:  0=missing/NA, 1=present - JSON
#     self.mask_seg4 = self.mask_seg5 = self.mask_seg6 = None # binary mask - 4 values:  0=missing/NA, 1=present - JSON
#     self.seg1_len = self.seg2_len = self.seg3_len = None    # in mm - length of the segment # todo
#     self.seg4_len = self.seg5_len = self.seg6_len = None    # in mm - length of the segment # todo
#     self.diam_tol_minus = None  # in mm - technical drawing # todo
#     self.diam_tol_plus = None   # in mm - technical drawing # todo
#     # GD&T related
#     self.tolerance_type = None  # binary mask - X values: 0=missing/NA, 1=present - technical drawing # todo
#     self.tolerance_value = None # in mm - tolerance value of the special tolerance - technical drawing # todo
#     # Context related
#     self.material = None                  # categorical index or learned embedding - technical drawing # todo
#     self.surface_finish_Ra = None         # in micro meters - technical drawing # todo
#     # Thread related
#     self.has_thread = None                # 0/1 - technical drawing # todo
#     self.thread_nominal_dia = None        # in mm - E.g., 2.5 for M2.5 - technical drawing # todo
#     self.thread_pitch = None              # in mm - E.g, 0.45 - technical drawing # todo
#     self.thread_depth = None              # in mm - engagement length; if THRU ALL, set to wall thickness - technical drawing # todo
#     self.thread_class_grade = None        # E.g., 6 for 6H or 6g - technical drawing # todo
#     self.thread_class_is_internal = None  # 0/1 - 1 for H/G (internal, 0 for h/g (external) - technical drawing # todo
#     # Counter Sink related
#     self.has_csk = None           # 0/1 - JSON # todo
#     self.csk_major_dia = None     # in mm - JSON # todo
#     self.csk_angle_deg = None     # in degree (not radians) - JSON # todo
#     # Counter Bore related
#     self.has_cbore = None         # in mm - JSON # todo
#     self.cbore_dia = None         # in mm - JSON # todo
#     self.cbore_depth = None       # in mm - JSON # todo
#     # Chamfer related
#     self.has_chamfer = None       # in mm - technical drawing # todo
#     self.chamfer_width = None     # in mm - technical drawing # todo
#     self.chamfer_depth = None     # in mm - technical drawing # todo
#     self.chamfer_angle_deg = None # degree - OPTIONAL - technical drawing # todo
#
#
#   def decide_params(self):
#     """ This method fills the fields for the ML model database"""
#     self.main_diameter = self.parent_hole_group.diameter
#     self.hole_depth = self.parent_hole_group.hole_depth
#
#     mask_str = str(self.parent_hole_group.parent_topology.topology_mask)  # Handling variable lengths (1-6 digits)
#     segs = mask_segments_compute(mask_str)
#     (self.mask_seg1, self.mask_seg2, self.mask_seg3, self.mask_seg4, self.mask_seg5, self.mask_seg6) = segs
#
#
#
#
#   def add_job(self, job, holes_group_info):
#     """
#     This method assigns a job to a hole.
#
#     Args:
#       job (dict): Holds all information about the job.
#       holes_group_info (dict): Holds all information about the hole group being processed
#     """
#
#     tool_type = process_tool_type_name(job['tool']['tool_type'])  # Cosmetics
#
#     new_job = Job(job, tool_type, holes_group_info)               # Creating a new Job instance
#     self.decide_thread_params(job)                                # Filling the thread parameters for relevant jobs
#
#     # Checking if this job is really new - acting as a fail-safe mechanism
#     new_job_flag = True
#     for existing_job in self.jobs:
#       if new_job == existing_job:
#         new_job_flag = False
#
#     # Adding the job only it's new
#     if new_job_flag:
#       self.jobs.append(new_job)
#
#
#   def decide_thread_params(self, job):
#     """
#     This function infers the thread parameters by looking at the tool parameters.
#
#     *Note: for now, I'm comparing only to the ISO Metric standard.
#
#     Args:
#       job (dict): Holds all information about the job.
#     """
#     # Known ISO Metric thread table (coarse and fine pitches)
#     metric_threads = {
#       1.2: [0.25], 1.4: [0.3], 1.6: [0.35], 2.0: [0.4], 2.2: [0.45], 2.5: [0.45], 3.0: [0.5], 3.5: [0.6], 4.0: [0.7],
#       5.0: [0.8], 6.0: [1.0], 7.0: [1.0], 8.0: [1.25, 1.0], 10.0: [1.5, 1.25, 1.0], 12.0: [1.75, 1.5, 1.25],
#       14.0: [2.0, 1.5], 16.0: [2.0, 1.5], 18.0: [2.5, 2.0, 1.5], 20.0: [2.5, 2.0, 1.5], 22.0: [2.5, 2.0, 1.5],
#       24.0: [3.0, 2.0], 27.0: [3.0, 2.0], 30.0: [3.5, 2.0], 33.0: [3.5, 2.0], 36.0: [4.0, 3.0], 39.0: [4.0, 3.0, 2.0],
#       42.0: [4.5, 3.0], 45.0: [4.5], 48.0: [5.0], 52.0: [5.0, 3.0], 56.0: [5.5, 4.0], 60.0: [5.5, 4.0],
#       64.0: [6.0, 4.0], 68.0: [6.0], 72.0: [6.0, 4.0], 80.0: [6.0, 4.0], 90.0: [6.0, 4.0], 100.0: [6.0, 4.0]
#     }
#
#     # Initialize
#     thread_flag = False
#     thread_or_tap = None
#     unit = None
#
#     # Choose which diameter parameter we're looking at - according to Thread Mill or Drill with Tap tool
#     if job["type"] == "NC_THREAD":
#       thread_or_tap = True
#       thread_flag = True
#     elif job["type"] == "NC_DRILL" and job["tool"]["tool_type"] == "TOOL_TAP_MILL":
#       thread_or_tap = False
#       thread_flag = True
#
#     # If thread_flag is False, then it's not Thread Milling or Drill with Tap
#     if not thread_flag:
#       return
#     else:
#       # Finding thread's depth value
#       if job.get("job_depth") >= self.parent_hole_group.hole_depth:
#         # True if job's depth is greater (or equal) than the hole's depth
#         self.thread_depth = self.parent_hole_group.hole_depth
#       else:
#         # True if job's depth is lesser than the hole's depth
#         self.thread_depth = job["job_depth"]
#
#       # Extract length parameters
#       diam_type = "MajorDiameter" if thread_or_tap else "D"
#       for param in job["tool"]["lengthParameters"]:
#         # Tap tool's head has a chamfer, so I subtract its value from the thread's depth
#         if not thread_or_tap and param["name"] == "Ch.L":
#           # True if it's Drill with Tap
#           self.thread_depth -= param["value"]
#         if param["name"] == diam_type:
#           self.thread_nominal_diameter = param["value"]   # Finding thread's nominal diameter value
#           unit = param["unit"]                            # Finding the units - mm/inch
#         elif param["name"] == "Pitch":
#           self.thread_pitch = param["value"]              # Finding thread's pitch value
#
#       # Finding thread's standard - checking if diameter and pitch matches ISO Metric table
#       if unit == "mm":
#         for dia, pitches in metric_threads.items():
#           if abs(self.thread_nominal_diameter - dia) < 0.2:  # Allow small tolerance
#             for p in pitches:
#               if abs(self.thread_pitch - p) < 0.05:          # Allow small tolerance
#                 self.standard = f"M{dia}_x_{self.thread_pitch}"
#


class Hole:
  """
  An object of this class holds a hole - it's position, tolerance, and jobs performed on it.
  """
  def __init__(self, new_coordinates, job, parent_hole_group):
    self.parent_hole_group = parent_hole_group  # pointer to the hole group which this hole belongs to
    self.center_coordinates = new_coordinates
    self.jobs = []  # The jobs performed on this hole by the order they were performed
    self.tolerance_type  = None
    self.upper_tolerance = None
    self.lower_tolerance = None

    # Threading attributes deducted from tool parameters
    self.thread_nominal_diameter = None    # float: Nominal diameter (in mm) of the thread, e.g., 8 for an M8 thread.
    self.thread_pitch            = None    # float: Thread pitch (in mm). E.g., 1.25 for M8x1.25
    self.standard                = None    # str:   The thread's standard
    self.thread_depth            = None    # float: The depth of the thread

    # todo I don't know YET how to compute the field below - data from the techinical drawing is needed
    self.thread_tolerance_class  = None    # str:   Thread tolerance class, defining the tolerance and fit for the thread. E.g., 6H.


  def add_job(self, job, holes_group_info):
    """
    This method assigns a job to a hole.

    Args:
      job (dict): Holds all information about the job.
      holes_group_info (dict): Holds all information about the hole group being processed
    """

    tool_type = process_tool_type_name(job['tool']['tool_type'])  # Cosmetics

    new_job = Job(job, tool_type, holes_group_info)               # Creating a new Job instance
    self.decide_thread_params(job)                                # Filling the thread parameters for relevant jobs

    # Checking if this job is really new - acting as a fail-safe mechanism
    new_job_flag = True
    for existing_job in self.jobs:
      if new_job == existing_job:
        new_job_flag = False

    # Adding the job only it's new
    if new_job_flag:
      self.jobs.append(new_job)


  def decide_thread_params(self, job):
    """
    This function infers the thread parameters by looking at the tool parameters.

    *Note: for now, I'm comparing only to the ISO Metric standard.

    Args:
      job (dict): Holds all information about the job.
    """
    # Known ISO Metric thread table (coarse and fine pitches)
    metric_threads = {
      1.2: [0.25], 1.4: [0.3], 1.6: [0.35], 2.0: [0.4], 2.2: [0.45], 2.5: [0.45], 3.0: [0.5], 3.5: [0.6], 4.0: [0.7],
      5.0: [0.8], 6.0: [1.0], 7.0: [1.0], 8.0: [1.25, 1.0], 10.0: [1.5, 1.25, 1.0], 12.0: [1.75, 1.5, 1.25],
      14.0: [2.0, 1.5], 16.0: [2.0, 1.5], 18.0: [2.5, 2.0, 1.5], 20.0: [2.5, 2.0, 1.5], 22.0: [2.5, 2.0, 1.5],
      24.0: [3.0, 2.0], 27.0: [3.0, 2.0], 30.0: [3.5, 2.0], 33.0: [3.5, 2.0], 36.0: [4.0, 3.0], 39.0: [4.0, 3.0, 2.0],
      42.0: [4.5, 3.0], 45.0: [4.5], 48.0: [5.0], 52.0: [5.0, 3.0], 56.0: [5.5, 4.0], 60.0: [5.5, 4.0],
      64.0: [6.0, 4.0], 68.0: [6.0], 72.0: [6.0, 4.0], 80.0: [6.0, 4.0], 90.0: [6.0, 4.0], 100.0: [6.0, 4.0]
    }

    # Initialize
    thread_flag = False
    thread_or_tap = None
    unit = None

    # Choose which diameter parameter we're looking at - according to Thread Mill or Drill with Tap tool
    if job["type"] == "NC_THREAD":
      thread_or_tap = True
      thread_flag = True
    elif job["type"] == "NC_DRILL" and job["tool"]["tool_type"] == "TOOL_TAP_MILL":
      thread_or_tap = False
      thread_flag = True

    # If thread_flag is False, then it's not Thread Milling or Drill with Tap
    if not thread_flag:
      return
    else:
      # Finding thread's depth value
      if job.get("job_depth") >= self.parent_hole_group.hole_depth:
        # True if job's depth is greater (or equal) than the hole's depth
        self.thread_depth = self.parent_hole_group.hole_depth
      else:
        # True if job's depth is lesser than the hole's depth
        self.thread_depth = job["job_depth"]

      # Extract length parameters
      diam_type = "MajorDiameter" if thread_or_tap else "D"
      for param in job["tool"]["lengthParameters"]:
        # Tap tool's head has a chamfer, so I subtract its value from the thread's depth
        if not thread_or_tap and param["name"] == "Ch.L":
          # True if it's Drill with Tap
          self.thread_depth -= param["value"]
        if param["name"] == diam_type:
          self.thread_nominal_diameter = param["value"]   # Finding thread's nominal diameter value
          unit = param["unit"]                            # Finding the units - mm/inch
        elif param["name"] == "Pitch":
          self.thread_pitch = param["value"]              # Finding thread's pitch value

      # Finding thread's standard - checking if diameter and pitch matches ISO Metric table
      if unit == "mm":
        for dia, pitches in metric_threads.items():
          if abs(self.thread_nominal_diameter - dia) < 0.2:  # Allow small tolerance
            for p in pitches:
              if abs(self.thread_pitch - p) < 0.05:          # Allow small tolerance
                self.standard = f"M{dia}_x_{self.thread_pitch}"



class Job:
  """
  An object of this class holds a job that is done on a hole.
  Each field holds the json's field with the same name.
  """
  def __init__(self, job, tool_type, holes_group_info):
    self.job_number = job["job_number"]           # Job's index in SolidCAM
    self.job_name = job['name']                   # Job name as defined by the user
    self.job_type = job['type']                   # Technology used (e.g, 2_5D_Drilling)
    self.tool_type = tool_type                    # Tool being used (e.g, End Mill)
    self.tool_parameters = job['tool']            # Tool parameters
    self.job_depth = job['job_depth']             # How deep the tool goes in, NOT taking into account the tool's tip
    self.tool_depth = None                        # How deep the tool goes in, taking into account the tool's tip
    self.thread_mill_params = job["thread_mill"]  # Thread Milling parameters - not None only on this job
    self.op_params = job["operation_parameters"]  # if job.get("operation_parameters") else None  # Profile & Chamfer parameters - not None only on those jobs
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

  def __eq__(self, other):
    """ Compare two Job objects by checking if all their attributes are identical. """
    if not isinstance(other, Job):
      return NotImplemented
    return self.__dict__ == other.__dict__

  def __repr__(self):
    """ Used for printing - Returns a string with Job type, Tool type, Job name and Job number """
    return 'Job type: {} | Tool type: {} | Job name and number: {} ({})'.format(self.job_type, self.tool_type, self.job_name, self.job_number)


  # todo need to change this function so it would stop referring drilling and non-drilling separately
  def decide_drill_params(self, job, holes_group_info):
    """
    This method decides the drill parameters for the job, depending on the job type.

    Args:
      job (dict): Holds all information about the job.
      holes_group_info (dict): Holds all information about the hole group being processed
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

    tool_angle = 0
    tool_depth = 0

    # Saving the tool's head angle
    for param in self.tool_parameters["lengthParameters"]:
      if param["name"] == "A":
        tool_angle = param["value"]
    for param in self.tool_parameters["parameters"]:
      if param["name"] == "A":
        tool_angle = param["value"]


    # True if the job is one of the drilling jobs
    if self.job_type in drilling_types and tool_angle != 0:
      tip_depth = self.depth_diameter_value / math.tan(math.radians(tool_angle))
      self.tool_depth = self.job_depth + tip_depth

    # todo Need to update this part once I have recognized hole groups in Profile and Chamfer jobs
    # todo It is crucial to update it because the tool Ball Nose doesn't have a flat head
    # True if the job in Profile or Chamfer
    elif self.job_type == ["NC_PROFILE"] or self.job_type == ["NC_CHAMFER"]:
      self.tool_depth = self.job_depth

    return tool_depth




