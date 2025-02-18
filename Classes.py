from MACs_Conversions import compare_coordinates, compare_geometries
from Utilities_and_Cosmetics import process_job_name, process_tool_type_name

bold_s = '\033[1m' # Start to write in bold
bold_e = '\033[0m' # End to write in bold

class Topology:
  """ An object of this class holds all the holes in the specified topology """
  def __init__(self, topology, topology_mask):
    self.topology = topology           # String containing topology's name (e.g, CounterBore)
    self.topology_mask = topology_mask # Int containing topology's mask
    self.holes_groups = []             # The hole groups that belong to this topology
    self.jobs_orders_dict = dict()     # Used for printing the legend in plots

  def add_hole_group(self, job, new_coordinates, new_geom_shape):
    """
    This method creates a new hole group to the relevant topology ONLY if the
    geometric shape of the hole group is new.
    If the geometric shape is not new, we just update the number of the instances
    in the hole group.
    """
    # Checking if the geometry shape already exists, and add if not
    for group in self.holes_groups:
      # if true, then geometry shape or its reverse already exists, so just updating number of centers
      if compare_geometries(new_geom_shape, group.geom_shape):
        # Going over the centers in the new coordinates in order to update centers
        for new_center in new_coordinates:
          # Going over all the jobs inside the hole group
          for existing_job in group.jobs:
            # Checking if the centers refer to the same hole
            if compare_coordinates(new_center, existing_job.centers, group.hole_depth,
                              job["home_number"], existing_job.parallel_home_numbers):
              group.centers.add(new_center)
        return group, False

    # The geometry shape doesn't exist, so we create a new group and add it
    new_group = HoleGroup(new_coordinates, new_geom_shape)
    self.holes_groups.append(new_group)
    return new_group, True

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
  """
  def __init__(self, new_coordinates, geom_shape):
    self.centers = set(new_coordinates)  # The (x,y) coordinates of holes in this hole group
    self.jobs = []                # The jobs performed on this hole group by the order they were performed
    self.jobs_order = ''          # A string that holds the order of the jobs
    self.geom_shape = geom_shape  # Geomertric shape of the holes in this hole group
    self.part_name       = None
    self.diameter        = None   # The smallest diameter of the holes
    self.hole_depth      = None
    self.thread_depth    = 0
    self.thread_diameter = 0
    self.thread_pitch    = 0

  def add_job(self, job, drill_job_flag, job_type, tool_type, tool_parameters, job_depth, new_coordinates, job_number):
    """
    This method assigns a job to a hole group ONLY if the same exact job doesn't
    already exist - we check for existence via comparison of job depth, job type,
    tool type, and tool parameters.
    """
    new_job_flag = True              # If stays True, then it is a new job
    job_type = process_job_name(job_type)    # Cosmetics
    tool_type = process_tool_type_name(tool_type) # Cosmetics
    if "ver" in tool_parameters:     # Removing unnecessary field from json: "ver" under tool_parameters
      tool_parameters.pop("ver")

    # Checking if the job already exists
    for existing_job in self.jobs:   # Going over all the existing jobs in that hole group
      # if true, then job already exists
      if (existing_job.job_depth       == job_depth and      # Same job depth
          existing_job.job_type        == job_type  and      # Same job type
          existing_job.tool_type       == tool_type and      # Same tool type
          existing_job.tool_parameters == tool_parameters):  # Same tool parameters
        new_job_flag = False
        break

    if new_job_flag:  # Add the job if it's new
      new_job = Job(job, drill_job_flag, job_type, tool_type,
                    tool_parameters, job_depth, new_coordinates, job_number)
      self.jobs.append(new_job)
      self.jobs_order += f"{new_job.job_type} - {new_job.tool_type} | "

  def update_parameters(self, holes_group_info, part_name):
    """
    This method update the parameters of a hole group.
    The update takes place only ONCE - when the group is created.
    """
    # Adding the holes group part name
    self.part_name = part_name
    # Calculating the hole's diameter - taking the MINIMAL radius
    geom_shape = holes_group_info["_geom_ShapePoly"]
    self.diameter = abs(2*min(item["p0"][0] for item in geom_shape))
    # Updating the hole's parameters
    self.hole_depth      = holes_group_info["_geom_depth"]           # Hole's depth
    self.thread_depth    = holes_group_info["_geom_thread_depth"]    # Hole's thread depth
    self.thread_diameter = holes_group_info["_geom_thread_diameter"] # Hole's thread diameter
    self.thread_pitch    = holes_group_info["_geom_thread_pitch"]    # Hole's thread pitch

  def print(self):
    """ This method prints selected fields from that hole group """
    print(f"Part name: {self.part_name}")
    print(f"Number of instances : {len(self.centers)}")
    print(f"Geometry shape: {self.geom_shape}") # Print when checking MACs
    print(f"Holes centers: {{{', '.join(f'({x}, {y}, {z})' for x, y, z in self.centers)}}}")  # For debugging
    print(f"Diameter: {self.diameter}")
    print(f"Depth: {round(self.hole_depth, 3)}")
    print(f"{bold_s}{len(self.jobs)} jobs total{bold_e} were performed on this hole group.\nThe order they're being exectued:")
    for i, job in enumerate(self.jobs):
      print(f"{i+1} - {job}")
    print('')


class Job:
  """
  An object of this class holds a job that is done on a hole.
  Each field holds the json's field with the same name.
  """
  def __init__(self, job, drill_job_flag, job_type, tool_type, tool_parameters, job_depth, new_coordinates, job_number):
    self.job_number = job_number            # Job's index in SolidCAM
    self.job_name = job['name']             # Job name as defined by the user
    self.centers = set(new_coordinates)     # The (x,y) coordinates of holes that are being worked by this job
    self.job_type = job_type                # Technology used (e.g, 2_5D_Drilling)
    self.tool_type = tool_type              # Tool being used (e.g, End Mill)
    self.tool_parameters = tool_parameters  # Tool parameters
    self.job_depth = job_depth
    self.home_number = job['home_number']
    self.parallel_home_numbers = job['home_vParallelHomeNumbers']

    # Only assign drill-related attributes if drill_job_flag is True
    drill = job.get("drill", {}) if drill_job_flag else {}
    cycle = drill.get("cycle", {})
    self.drill_cycle_type = cycle.get("drill_type")
    self.drill_gcode_name = cycle.get("gcode_name")
    self.drill_params =     cycle.get("params")
    self.cycle_is_using =         drill.get("cycle_isUsing")
    self.depth_diameter_value =   drill.get("depth_diameter_value")
    self.depth_is_cutter_tip =    drill.get("depth_is_cutter_tip")
    self.depth_is_full_diameter = drill.get("depth_is_full_diameter")
    self.depth_is_tool_Diameter = drill.get("depth_is_tool_Diameter")

  def __repr__(self):
    # return 'Job type & Tool type: {}, Job name: {}'.format(f"{self.job_type} - {self.tool_type}", self.job_name)
    return 'Job type: {}, Tool type: {}, Job name and number: {} ({})'.format(self.job_type, self.tool_type, self.job_name, self.job_number)