# arctos_vr

## Purpose
Virtual Reality integration and visualization for the ICF dissertation system.
Provides immersive calibration interface, real-time visualization, and user interaction feedback.

## Planned Nodes
- `vr_interface_node`: Bridges VR system with ROS 2 ecosystem
- `visualization_server`: Renders real-time 3D visualization
- `interaction_handler`: Processes VR user input

## Planned Topics
**Subscribers:**
- `/robot/joint_states` (sensor_msgs/JointState)
- `/perception/poses` (from arctos_perception)
- `/calibration/results` (from arctos_calibration)

**Publishers:**
- `/vr/commands` (custom VRCommand messages)
- `/vr/visualization` (custom VizState messages)

## Dissertation Relevance
**User Interface Layer**: Enables intuitive monitoring and control of calibration process.
Supports "Immersive Calibration" aspect of dissertation title.
Facilitates user studies and validation experiments.

## Package Structure
```
arctos_vr/
├── README.md                      # This file
├── package.xml                    # VR SDK dependencies
├── arctos_vr/
│   ├── __init__.py
│   ├── vr_node.py                # Main VR integration node
│   └── visualization/             # Placeholder for VR UI components
└── setup.py / setup.cfg\n```

## Next Steps
1. Select and integrate VR framework (OpenXR, HTC Vive, Meta Quest, etc.)
2. Implement 3D scene rendering
3. Add gesture recognition for user interaction
4. Create calibration UI widgets for VR environment
