# TwinState.msg
# Canonical synchronized digital twin state
# Published by arctos_twin to report real-vs-sim synchronization state

std_msgs/Header header

# Joint state representing the current canonical twin estimate
sensor_msgs/JointState joint_state

# Estimated end-effector pose of the twin
geometry_msgs/PoseStamped end_effector_pose

# Time offset between real and simulated environments
builtin_interfaces/Duration time_offset

# Synchronization quality: 0.0 = poor, 1.0 = perfect
float32 sync_quality
