# CalibrationModel.msg
# Calibration Parameter Estimation MVP output
# Represents estimated geometric calibration parameters for dissertation evidence.

float64[] joint_zero_offsets
float64[] link_length_errors

float64 base_offset_x
float64 base_offset_y
float64 base_offset_z

float64 tool_offset_x
float64 tool_offset_y
float64 tool_offset_z

float64 confidence
