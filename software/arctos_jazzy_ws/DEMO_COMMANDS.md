# Arctos Calibration Framework — Demo Commands

**Milestone:** dissertation-framework-v6

## Prerequisites

In every terminal, first run:
```bash
source /opt/ros/jazzy/setup.bash
source ~/Immersive-Calibration-Framework/software/arctos_jazzy_ws/install/setup.bash
```

## Terminal 1 — Gazebo Simulation

```bash
ros2 launch arctos_description simulation.launch.py
```
Wait ~15 seconds for `arm_position_controller` to load.

## Terminal 2 — Full Calibration Pipeline

```bash
ros2 launch arctos_bringup arctos_bringup.launch.py \
  perception_mode:=sim_detection enable_solver:=true
```

Launches: twin_monitor, sync_error, sim_apriltag_detection, tag_pose,
calibration_observer, calibration_manager, calibration_solver, metrics.

Other perception modes:
```bash
# Mock (fixed pose, no camera)
ros2 launch arctos_bringup arctos_bringup.launch.py perception_mode:=mock enable_solver:=true

# Real AprilTag (requires camera topics)
ros2 launch arctos_bringup arctos_bringup.launch.py perception_mode:=apriltag enable_solver:=true
```

## Terminal 3 — Joint Motion Demo

```bash
ros2 launch arctos_twin joint_motion_demo.launch.py
```
Drives joint1 with a sine wave (±0.3 rad, 0.2 Hz).

## Terminal 4 — Topic Verification

```bash
ros2 topic list | grep arctos
ros2 topic echo /arctos/calibration/solution --once
ros2 topic echo /arctos/evaluation/metrics --once
```

## Expected Topics

| Topic | Type | What it proves |
|-------|------|----------------|
| `/joint_states` | JointState | Gazebo ros2_control bridge works |
| `/arctos/twin/state` | TwinState | Digital twin receives and wraps joint data |
| `/arctos/twin/sync_error` | JointState | Twin vs real error computation is live |
| `/arctos/perception/reference_frame_pose` | PoseStamped | Perception source provides reference poses |
| `/arctos/calibration/result` | CalibrationResult | Observer produces calibration observations |
| `/arctos/calibration/state` | Float64MultiArray | Manager tracks running statistics |
| `/arctos/calibration/solution` | CalibrationResult | Solver computes improvement estimates |
| `/arctos/evaluation/metrics` | Float64MultiArray | Unified metrics from twin + calibration |
| `/arm_position_controller/commands` | Float64MultiArray | Joint commands reach the controller |

## Known Limitations

- **AprilTag sim_detection** is a synthetic test bridge, not a real camera pipeline.
- **Calibration solver** is an MVP residual tracker, not a final DH parameter optimiser.
- **Real camera / real robot** integration is pending.
- **VR package (arctos_vr)** is scaffold only — no nodes implemented.
- **PerceptionQuality** message is defined but not published by any node yet.
- **Sync error** is zero in passthrough mode since twin mirrors real joint states directly.

## Helper Scripts

```bash
bash scripts/run_demo_stack.sh              # Print demo instructions
bash scripts/run_demo_stack.sh --check      # Verify packages + interfaces
bash scripts/run_demo_stack.sh --topics     # List active topics
bash scripts/run_demo_stack.sh --commands   # Print copy-paste commands
bash scripts/demo_check.sh                  # Full validation (12 checks)
bash scripts/demo_check.sh --live           # + live topic verification
```
