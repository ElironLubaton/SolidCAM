# @title Converting inch to mm

# """
# This cell will be used only once we're sure we know which fields we should
# convert from inch to mm.
# """

# def inches_to_mm(inches):
#   """ Converts inches to millimeters """
#   return round(inches*25.4, 3)

# def convert_json_units(data, exclude_fields=None):
#   """ Converting entire JSON file units from inch to mm """
#   # fields I want to exclude for various reasons
#   exclude_fields = ["coolant", "cycle", "ver", "usage_index", "home_number",
#                     "home_MAC", "home_position", "home_vParallelHomeNumbers",
#                     "job_feed", "job_holeWzrd_id", "job_spin", "max_power",
#                     "max_spin", "tool", "home_matrix"]

#   # Recursively process dictionaries
#   if isinstance(data, dict):
#     converted_data = {}
#     for key, value in data.items():
#       if key in exclude_fields:
#         # Keep the field as is if it's in the exclude list
#         converted_data[key] = value
#       elif key == "lengthParameters" and isinstance(value, list):
#         # Special handling for "lengthParameters"
#         converted_data[key] = [
#                   {**param,
#                     "value": inches_to_mm(param["value"]) if param.get("unit") == "inch" else param["value"],
#                     "unit": "mm" if param.get("unit") == "inch" else param.get("unit")}
#                   for param in value]
#       else:
#         # Recursively handle the value
#         converted_data[key] = convert_json_units(value, exclude_fields)
#     return converted_data

#   # Recursively process lists
#   elif isinstance(data, list):
#    return [convert_json_units(item) for item in data]
#   # Convert numeric values (excluding strings and booleans)
#   elif isinstance(data, (int, float)) and not isinstance(data, bool):
#     return inches_to_mm(data)
#   # Return the value as is for strings, booleans, or other types
#   return data









