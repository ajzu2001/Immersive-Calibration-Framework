# HardwareJointState.msg
# MVP hardware sensor acquisition message for future ESP32 + AS5600 + limits + IMU.

std_msgs/Header header
string[] joint_names
float64[] encoder_positions
bool[] limit_switch_min
bool[] limit_switch_max
float64 imu_roll
float64 imu_pitch
float64 imu_yaw
float64 confidence
