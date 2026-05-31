# arctos_twin

## Purpose
Digital twin and virtual environment synchronization for the ICF dissertation system.
Maintains synchronized simulation state with real robot, enabling physics-based calibration validation.

## Planned Nodes
- `twin_sync_node`: Keeps virtual and real robot synchronized
- `state_broadcaster`: Publishes current twin state

## Planned Topics
**Subscribers:**
- `/robot/joint_states` (sensor_msgs/JointState)
- `/robot/ee_pose` (geometry_msgs/PoseStamped)

**Publishers:**
- `/twin/state` (custom TwinState messages)
- `/twin/sim_poses` (geometry_msgs/PoseArray)

## Dissertation Relevance
**Architecture Key**: Enables comparative analysis between real and simulated robot behavior.
Central to dissertation's hypothesis on calibration accuracy validation.

## Package Structure
```
arctos_twin/
├── README.md                    # This file
├── package.xml                  # Dependencies on rclpy, geometry_msgs
├── arctos_twin/
│   ├── __init__.py
│   └── twin_node.py            # Placeholder node (Phase 0)
└── setup.py / setup.cfg
```

## Next Steps
1. Interface with Gazebo simulation (arctos_description)
2. Implement state synchronization logic
3. Add TF frame management for virtual poses
4. Create performance benchmarks
