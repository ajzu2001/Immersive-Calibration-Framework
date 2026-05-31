# Arctos Immersive Calibration Framework — Status Report V1

**Date:** 2026-05-31
**Branch:** main
**ROS 2 Distribution:** Jazzy
**Workspace:** `arctos_jazzy_ws`

---

## 1. Package Overview

| Package | Build Type | Status | Nodes |
|---------|-----------|--------|-------|
| arctos_description | ament_cmake | Complete (pre-existing) | — (launch only) |
| arctos_interfaces | ament_cmake + rosidl | Complete | — (messages only) |
| arctos_perception | ament_python | MVP implemented | 1 |
| arctos_twin | ament_python | MVP implemented | 2 |
| arctos_calibration | ament_python | MVP implemented | 2 |
| arctos_evaluation | ament_python | MVP implemented | 1 |
| arctos_vr | ament_python | Scaffold only | 0 |

All 7 packages build successfully with `colcon build --symlink-install`.

---

## 2. Implemented Nodes

### arctos_perception
- **mock_tag_pose_node** — Publishes a fixed `PoseStamped` at 10 Hz with configurable position and optional Gaussian noise. Parameters: `frame_id`, `pos_x`, `pos_y`, `pos_z`, `noise_stddev`.

### arctos_twin
- **twin_monitor_node** — Subscribes to `/joint_states`, wraps into `TwinState`, publishes on `/arctos/twin/state` at incoming rate. Sets `sync_quality = 1.0` (passthrough).
- **sync_error_node** — Subscribes to both `/joint_states` and `/arctos/twin/state`, matches joints by name, computes per-joint position error (twin − real), publishes on `/arctos/twin/sync_error`.

### arctos_calibration
- **calibration_observer_node** — Subscribes to `/arctos/perception/reference_frame_pose`, computes position error magnitude (`sqrt(x²+y²+z²)`), publishes `CalibrationResult` on `/arctos/calibration/result`. Logs at 1 Hz.
- **calibration_manager_node** — Subscribes to `/arctos/calibration/result`, maintains running statistics (count, latest/best/average residual), publishes state vector on `/arctos/calibration/state`. Logs at 1 Hz.

### arctos_evaluation
- **metrics_node** — Subscribes to `/arctos/twin/sync_error` and `/arctos/calibration/state`. Computes mean/max/RMS twin error, merges with calibration statistics, publishes 6-element vector on `/arctos/evaluation/metrics`. Logs at 1 Hz.

---

## 3. Topic Map

### Published Topics

| Topic | Type | Publisher |
|-------|------|----------|
| `/joint_states` | `sensor_msgs/JointState` | External (joint_state_publisher_gui / Gazebo) |
| `/arctos/twin/state` | `arctos_interfaces/TwinState` | twin_monitor_node |
| `/arctos/twin/sync_error` | `sensor_msgs/JointState` | sync_error_node |
| `/arctos/perception/reference_frame_pose` | `geometry_msgs/PoseStamped` | mock_tag_pose_node |
| `/arctos/calibration/result` | `arctos_interfaces/CalibrationResult` | calibration_observer_node |
| `/arctos/calibration/state` | `std_msgs/Float64MultiArray` | calibration_manager_node |
| `/arctos/evaluation/metrics` | `std_msgs/Float64MultiArray` | metrics_node |

### Subscription Map

| Node | Subscribes To |
|------|--------------|
| twin_monitor_node | `/joint_states` |
| sync_error_node | `/joint_states`, `/arctos/twin/state` |
| calibration_observer_node | `/arctos/perception/reference_frame_pose` |
| calibration_manager_node | `/arctos/calibration/result` |
| metrics_node | `/arctos/twin/sync_error`, `/arctos/calibration/state` |

---

## 4. Message Flow

```
/joint_states (external)
    │
    ├──► twin_monitor_node ──► /arctos/twin/state
    │                                │
    └──► sync_error_node ◄───────────┘
              │
              └──► /arctos/twin/sync_error ──► metrics_node
                                                    ▲
/arctos/perception/reference_frame_pose             │
    │  (mock_tag_pose_node)                         │
    │                                               │
    └──► calibration_observer_node                  │
              │                                     │
              └──► /arctos/calibration/result        │
                        │                           │
                        └──► calibration_manager_node
                                  │
                                  └──► /arctos/calibration/state ───┘
                                                          │
                                                          ▼
                                              /arctos/evaluation/metrics
```

---

## 5. Launch Files

| Package | Launch File | Nodes Launched |
|---------|------------|----------------|
| arctos_description | display.launch.py | robot_state_publisher, joint_state_publisher_gui, rviz2 |
| arctos_description | simulation.launch.py | Gazebo simulation stack |
| arctos_description | gazebo.launch.py | Gazebo integration |
| arctos_perception | perception.launch.py | mock_tag_pose_node |
| arctos_twin | twin_monitor.launch.py | twin_monitor_node |
| arctos_twin | twin_sync.launch.py | twin_monitor_node + sync_error_node |
| arctos_calibration | calibration_observer.launch.py | calibration_observer_node |
| arctos_calibration | calibration_manager.launch.py | calibration_manager_node |
| arctos_evaluation | evaluation.launch.py | metrics_node |

---

## 6. Custom Message Definitions (arctos_interfaces)

### TwinState.msg
- `std_msgs/Header header`
- `sensor_msgs/JointState joint_state`
- `geometry_msgs/PoseStamped end_effector_pose`
- `builtin_interfaces/Duration time_offset`
- `float32 sync_quality`

### CalibrationResult.msg
- `std_msgs/Header header`
- `string calibration_id`
- `float64[] parameters`
- `float64 residual_error`
- `uint32 iterations`
- `uint8 convergence_status`
- `float64 execution_time`

### PerceptionQuality.msg
- `std_msgs/Header header`
- `float32 overall_score`
- `float32 detection_confidence`
- `float32 tracking_consistency`
- `uint32 num_detections`
- `uint32 processing_time_ms`
- `string status_message`

---

## 7. Real vs Mocked Components

### Real / Functional
- **arctos_description**: Complete URDF/Xacro, meshes, Gazebo worlds, RViz configs, controller config
- **arctos_interfaces**: All 3 message types generated and usable
- **twin_monitor_node**: Real passthrough (copies joint states into TwinState)
- **sync_error_node**: Real per-joint error computation
- **calibration_manager_node**: Real running statistics aggregation
- **metrics_node**: Real metric computation and aggregation from both pipelines

### Mocked / Placeholder
- **mock_tag_pose_node**: Publishes a fixed pose — no real camera or AprilTag detection
- **calibration_observer_node**: Computes position magnitude as residual — no real calibration optimisation
- **twin_monitor_node** end-effector pose: Identity placeholder — no forward kinematics
- **PerceptionQuality.msg**: Defined but not published by any node yet

---

## 8. Remaining Work: AprilTag-Based Calibration

### Priority 1 — Camera & Detection Pipeline
1. Integrate a camera driver node (e.g. `usb_cam` or `realsense2_camera`)
2. Replace `mock_tag_pose_node` with a real AprilTag detector (e.g. `apriltag_ros` or `isaac_ros_apriltag`)
3. Publish detected tag poses as `geometry_msgs/PoseStamped` on the existing topic
4. Publish `PerceptionQuality` from the detection node

### Priority 2 — Forward Kinematics in Twin
5. Wire forward kinematics into `twin_monitor_node` to compute real `end_effector_pose` from joint states (using URDF or KDL)
6. Update `sync_quality` based on actual measurement comparison

### Priority 3 — Calibration Optimisation
7. Implement a real calibration solver in `calibration_observer_node` (e.g. least-squares DH parameter optimisation)
8. Accumulate observation pairs (measured tag pose vs FK-predicted pose)
9. Solve for parameter corrections and populate `CalibrationResult.parameters` with real DH offsets
10. Update `convergence_status` and `iterations` from actual optimiser state

### Priority 4 — Calibration Application
11. Create a node or service to apply calibrated parameters back to the robot model
12. Close the loop: re-measure after calibration to verify improvement

---

## 9. Remaining Work: VR-Assisted Calibration

### arctos_vr Package (currently scaffold only)
1. **VR bridge node**: Subscribe to VR controller poses (from SteamVR/OpenXR via a bridge like `openxr_ros2`) and publish as `geometry_msgs/PoseStamped`
2. **VR teleoperation node**: Map VR controller input to joint commands, publish to `/joint_states` or a command topic
3. **VR visualisation**: Stream robot state and calibration data back to VR headset (e.g. via WebSocket or shared-memory bridge to Unity/Unreal)
4. **Immersive calibration workflow**: Allow user to physically guide calibration poses in VR, triggering calibration observations at each pose
5. **VR-specific launch file**: Bring up VR bridge + teleoperation + twin pipeline together

### Integration Points
- VR controller poses → replaces or supplements AprilTag poses as calibration reference
- VR joint commands → `/joint_states` → twin pipeline (already wired)
- `/arctos/evaluation/metrics` → VR overlay for real-time calibration feedback

---

## 10. Recommended Next Implementation Order

1. **Forward kinematics in twin_monitor_node** — High value, unblocks real twin error measurement
2. **Real AprilTag perception** — Replace mock with `apriltag_ros`, requires camera hardware
3. **Calibration solver** — Implement least-squares optimisation using accumulated pose pairs
4. **PerceptionQuality publisher** — Wire into the real detection node
5. **Unified system launch file** — Single launch bringing up the full pipeline
6. **VR bridge node** — First VR integration point
7. **VR teleoperation** — Interactive pose collection for calibration
8. **VR visualisation overlay** — Immersive calibration feedback

---

## 11. Workspace File Structure

```
src/
├── arctos_description/       # ament_cmake — URDF, meshes, launch, RViz, Gazebo
│   ├── urdf/
│   ├── meshes/
│   ├── launch/
│   ├── config/
│   ├── rviz/
│   └── worlds/
├── arctos_interfaces/        # ament_cmake — TwinState, CalibrationResult, PerceptionQuality
│   ├── msg/
│   └── CMakeLists.txt
├── arctos_perception/        # ament_python — mock_tag_pose_node
│   ├── arctos_perception/
│   └── launch/
├── arctos_twin/              # ament_python — twin_monitor_node, sync_error_node
│   ├── arctos_twin/
│   └── launch/
├── arctos_calibration/       # ament_python — calibration_observer_node, calibration_manager_node
│   ├── arctos_calibration/
│   └── launch/
├── arctos_evaluation/        # ament_python — metrics_node
│   ├── arctos_evaluation/
│   └── launch/
└── arctos_vr/                # ament_python — scaffold only, no nodes
    └── arctos_vr/
```
