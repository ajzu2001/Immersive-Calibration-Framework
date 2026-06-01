#!/usr/bin/env bash
# run_demo_stack.sh — Arctos Calibration Framework demo helper
# dissertation-framework-v6
#
# Usage:
#   bash scripts/run_demo_stack.sh               # print terminal instructions
#   bash scripts/run_demo_stack.sh --check        # verify packages + interfaces
#   bash scripts/run_demo_stack.sh --topics       # list active arctos topics
#   bash scripts/run_demo_stack.sh --commands      # print copy-paste commands only

set -o pipefail

WS_DIR="$(cd "$(dirname "$0")/.." && pwd)"

source_env() {
    source /opt/ros/jazzy/setup.bash 2>/dev/null
    source "$WS_DIR/install/setup.bash" 2>/dev/null
}

case "${1:-}" in
    --check)
        source_env
        echo "=== Package check ==="
        PASS=0; FAIL=0
        for pkg in arctos_description arctos_interfaces arctos_perception arctos_twin arctos_calibration arctos_evaluation arctos_bringup arctos_vr; do
            if ros2 pkg prefix "$pkg" &>/dev/null; then
                echo "  [OK] $pkg"; ((PASS++))
            else
                echo "  [MISSING] $pkg"; ((FAIL++))
            fi
        done
        echo ""
        echo "=== Interface check ==="
        for iface in arctos_interfaces/msg/TwinState arctos_interfaces/msg/CalibrationResult arctos_interfaces/msg/PerceptionQuality; do
            if ros2 interface show "$iface" &>/dev/null; then
                echo "  [OK] $iface"; ((PASS++))
            else
                echo "  [MISSING] $iface"; ((FAIL++))
            fi
        done
        echo ""
        echo "$PASS passed, $FAIL failed"
        exit $FAIL
        ;;

    --topics)
        source_env
        echo "=== Active Arctos topics ==="
        ros2 topic list 2>/dev/null | grep -E "(arctos|joint_states|arm_position)" | sort
        ;;

    --commands)
        cat <<'EOF'
# Terminal 1 — Gazebo simulation
source /opt/ros/jazzy/setup.bash
source ~/Immersive-Calibration-Framework/software/arctos_jazzy_ws/install/setup.bash
ros2 launch arctos_description simulation.launch.py

# Terminal 2 — Full calibration pipeline
source /opt/ros/jazzy/setup.bash
source ~/Immersive-Calibration-Framework/software/arctos_jazzy_ws/install/setup.bash
ros2 launch arctos_bringup arctos_bringup.launch.py perception_mode:=sim_detection enable_solver:=true

# Terminal 3 — Joint motion demo
source /opt/ros/jazzy/setup.bash
source ~/Immersive-Calibration-Framework/software/arctos_jazzy_ws/install/setup.bash
ros2 launch arctos_twin joint_motion_demo.launch.py

# Terminal 4 — Topic monitoring
source /opt/ros/jazzy/setup.bash
source ~/Immersive-Calibration-Framework/software/arctos_jazzy_ws/install/setup.bash
ros2 topic list | grep arctos
ros2 topic echo /arctos/calibration/solution --once
ros2 topic echo /arctos/evaluation/metrics --once
EOF
        ;;

    *)
        cat <<'EOF'
╔═══════════════════════════════════════════════════════════════╗
║   Arctos Immersive Calibration Framework — Demo Guide        ║
║   dissertation-framework-v6                                  ║
╚═══════════════════════════════════════════════════════════════╝

Open 4 terminals. In each, first run:

  source /opt/ros/jazzy/setup.bash
  source ~/Immersive-Calibration-Framework/software/arctos_jazzy_ws/install/setup.bash

Then:

  TERMINAL 1 — Gazebo Simulation
  ros2 launch arctos_description simulation.launch.py
  (Wait ~15 seconds for controller to load)

  TERMINAL 2 — Calibration Pipeline
  ros2 launch arctos_bringup arctos_bringup.launch.py \
    perception_mode:=sim_detection enable_solver:=true

  TERMINAL 3 — Joint Motion Demo
  ros2 launch arctos_twin joint_motion_demo.launch.py

  TERMINAL 4 — Verify Topics
  ros2 topic list | grep arctos
  ros2 topic echo /arctos/calibration/solution --once
  ros2 topic echo /arctos/evaluation/metrics --once

Expected:
  - Robot base stays fixed in Gazebo
  - Joint 1 oscillates visibly
  - All /arctos/* topics are active

Helper options:
  bash scripts/run_demo_stack.sh --check     Verify packages
  bash scripts/run_demo_stack.sh --topics    List active topics
  bash scripts/run_demo_stack.sh --commands  Print copy-paste commands
EOF
        ;;
esac
