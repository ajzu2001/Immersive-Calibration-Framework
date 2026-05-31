# arctos_perception

## Purpose
Computer vision and perception pipeline for the ICF dissertation system.
Processes camera/sensor inputs to detect targets, extract features, and generate perception-based measurements for calibration.

## Planned Nodes
- `perception_node`: Main pipeline executor
- `feature_detector`: Extracts calibration markers/features from images
- `pose_estimator`: Estimates 6D pose from detected features

## Planned Topics
**Subscribers:**
- `/camera/rgb/image_raw` (sensor_msgs/Image)
- `/camera/depth/image_raw` (sensor_msgs/Image)

**Publishers:**
- `/perception/detections` (custom Detection messages)
- `/perception/poses` (geometry_msgs/PoseStamped)
- `/perception/debug/visualizations` (sensor_msgs/Image)

## Dissertation Relevance
**Critical Component**: Bridges physical robot perception with calibration workflow.
Enables data-driven evaluation of calibration quality in Phase 2-3.
Modular design allows independent algorithm iteration for MSc research.

## Package Structure
```
arctos_perception/
├── README.md                           # This file
├── package.xml                         # Dependencies on OpenCV, sensor_msgs
├── arctos_perception/
│   ├── __init__.py
│   └── perception_node.py             # Placeholder node (Phase 0)
└── setup.py / setup.cfg               # Entry points
```

## Next Steps
1. Integrate camera drivers and calibration data
2. Implement feature detection algorithms
3. Add ROS 2 publishers/subscribers
4. Create unit tests for perception pipeline
