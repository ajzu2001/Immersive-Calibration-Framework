# Arctos Calibration Framework — Demo Commands

## 1. Start Simulation (provides /joint_states)

```bash
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 launch arctos_description simulation.launch.py
```

## 2. Start Full Software Bringup

Open a **second terminal** and run one of:

```bash
# Mock perception (fixed pose, no camera needed)
ros2 launch arctos_bringup arctos_bringup.launch.py perception_mode:=mock

# Simulated AprilTag detection (fake detections + TF, tests full tag pipeline)
ros2 launch arctos_bringup arctos_bringup.launch.py perception_mode:=sim_detection

# Real AprilTag detection (requires camera image topics)
ros2 launch arctos_bringup arctos_bringup.launch.py perception_mode:=apriltag
```

For simulation clock:
```bash
ros2 launch arctos_bringup arctos_bringup.launch.py perception_mode:=mock use_sim_time:=true
```

## 3. Verify Topics

```bash
# Perception output (pose fed to calibration)
ros2 topic echo /arctos/perception/reference_frame_pose --once

# Perception quality (only in sim_detection/apriltag modes)
ros2 topic echo /arctos/perception/quality --once

# Calibration residual per observation
ros2 topic echo /arctos/calibration/result --once

# Calibration running statistics [count, latest, best, avg]
ros2 topic echo /arctos/calibration/state --once

# Digital twin state (requires /joint_states)
ros2 topic echo /arctos/twin/state --once

# Twin sync error (requires /joint_states)
ros2 topic echo /arctos/twin/sync_error --once

# Aggregated evaluation [mean_tw, max_tw, rms_tw, latest_cal, best_cal, avg_cal]
ros2 topic echo /arctos/evaluation/metrics --once
```

## 4. Expected Output

### perception/reference_frame_pose
Position values near the configured pose. In sim_detection mode: `x≈0.35, y≈0.0, z≈-0.10` with small noise.

### calibration/state
```
data: [<count>, <latest_residual>, <best_residual>, <avg_residual>]
```
Residual is the Euclidean distance of the detected pose from origin. In sim_detection mode, expect `≈0.36 m`.

### evaluation/metrics
```
data: [<mean_twin_err>, <max_twin_err>, <rms_twin_err>, <latest_cal>, <best_cal>, <avg_cal>]
```
Twin errors are 0.0 when no `/joint_states` source is running. Calibration values match `/arctos/calibration/state`.

## 5. What Each Topic Proves

- **reference_frame_pose** — Perception source is publishing pose data
- **quality** — Detection confidence and tracking consistency are reported
- **calibration/result** — Observer converts raw pose into calibration residual
- **calibration/state** — Manager aggregates residuals and tracks improvement
- **twin/state** — Robot joint states are mirrored into the digital twin
- **twin/sync_error** — Per-joint error between real and twin is computed
- **evaluation/metrics** — Both pipelines (twin + calibration) are fused into a single metric vector
