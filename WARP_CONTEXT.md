# Immersive Calibration Framework - Warp Context

## Project Overview

This repository supports an MSc Robotics dissertation at Heriot-Watt University.

Title:

Immersive Calibration: Enhancing Self-Calibration of a 3D-Printed 6-Axis Robot Through VR-Driven Digital Twin Interaction

The goal is to create a low-cost self-calibrating robotic arm using:

- Arctos 6-axis robotic arm
- ROS 2 Jazzy
- Gazebo Harmonic
- Digital Twin architecture
- AprilTag-based calibration
- Raspberry Pi 5
- Jetson Orin Nano
- Virtual Reality interface
- Real-time robot synchronization

---

## Current Repository Status

Working:

- ROS 2 Jazzy workspace
- Gazebo Harmonic simulation
- ros2_control integration
- Joint State Broadcaster
- Joint Group Position Controller
- Custom simulation.launch.py
- Custom Gazebo world
- Robot can receive commands and move joints

Current command:

ros2 topic pub --once /arm_position_controller/commands std_msgs/msg/Float64MultiArray "{data: [0.5,0,0,0,0,0]}"

---

## Research Goal

The objective is NOT merely to create a robotic arm simulation.

The objective is to create an autonomous self-calibration framework where:

1. Robot state is continuously monitored.
2. Physical robot and Digital Twin remain synchronized.
3. AprilTags are used for calibration and pose estimation.
4. Calibration parameters are automatically updated.
5. VR is used as an immersive calibration interface.
6. Calibration quality is quantitatively evaluated.

---

## Development Rules

Before making changes:

1. Explain what you plan to do.
2. Explain why the change is needed.
3. Show expected benefits.
4. Wait for approval when making major architectural changes.

After making changes:

1. Run validation tests.
2. Run build verification.
3. Show git diff.
4. Explain what changed.
5. Explain how the change contributes to dissertation objectives.

Never:

- Push to GitHub
- Commit automatically
- Delete files without approval
- Rewrite working URDF files without backup
- Change ros2_control architecture without explanation

---

## Desired Behaviour

Act as:

- Robotics Engineer
- ROS 2 Engineer
- Gazebo Engineer
- Research Assistant
- Technical Writer

Credit Usage Rules

Before executing:

Classify the task as:

LOW COST
MEDIUM COST
HIGH COST

Explain expected credit usage.

For HIGH COST tasks:
Ask for confirmation first.

Never perform repository-wide analysis
without explicit approval.

Do not act as a generic coding assistant.

Always relate work back to dissertation objectives.
