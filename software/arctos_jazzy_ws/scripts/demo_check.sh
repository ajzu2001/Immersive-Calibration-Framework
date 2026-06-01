#!/usr/bin/env bash
# demo_check.sh — Arctos Calibration Framework demo validation
# dissertation-framework-v6
#
# Usage:
#   bash scripts/demo_check.sh          # check packages + interfaces only
#   bash scripts/demo_check.sh --live   # also verify running topics

set -o pipefail

WS_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PASS=0
FAIL=0

pass() { echo "  [PASS] $1"; ((PASS++)); }
fail() { echo "  [FAIL] $1"; ((FAIL++)); }

# ── 1. Source environment ────────────────────────────────────────
echo "=== Sourcing ROS 2 Jazzy + workspace ==="
if [ -f /opt/ros/jazzy/setup.bash ]; then
    source /opt/ros/jazzy/setup.bash
    pass "ROS 2 Jazzy sourced"
else
    fail "ROS 2 Jazzy not found at /opt/ros/jazzy/setup.bash"
fi

if [ -f "$WS_DIR/install/setup.bash" ]; then
    source "$WS_DIR/install/setup.bash"
    pass "Workspace install sourced"
else
    fail "Workspace not built — run: colcon build --symlink-install"
fi

# ── 2. Check packages ───────────────────────────────────────────
echo ""
echo "=== Package check ==="
PACKAGES=(
    arctos_description
    arctos_interfaces
    arctos_perception
    arctos_twin
    arctos_calibration
    arctos_evaluation
    arctos_bringup
    arctos_vr
)
for pkg in "${PACKAGES[@]}"; do
    if ros2 pkg prefix "$pkg" &>/dev/null; then
        pass "$pkg"
    else
        fail "$pkg not found"
    fi
done

# ── 3. Check interfaces ─────────────────────────────────────────
echo ""
echo "=== Interface check ==="
INTERFACES=(
    arctos_interfaces/msg/TwinState
    arctos_interfaces/msg/CalibrationResult
    arctos_interfaces/msg/PerceptionQuality
)
for iface in "${INTERFACES[@]}"; do
    if ros2 interface show "$iface" &>/dev/null; then
        pass "$iface"
    else
        fail "$iface not found"
    fi
done

# ── 4. Check key executables ─────────────────────────────────────
echo ""
echo "=== Executable check ==="
EXECS=(
    "arctos_twin twin_monitor_node"
    "arctos_twin sync_error_node"
    "arctos_twin joint_command_demo_node"
    "arctos_perception mock_tag_pose_node"
    "arctos_calibration calibration_observer_node"
    "arctos_calibration calibration_manager_node"
    "arctos_calibration calibration_solver_node"
    "arctos_evaluation metrics_node"
)
for entry in "${EXECS[@]}"; do
    pkg=$(echo "$entry" | cut -d' ' -f1)
    exe=$(echo "$entry" | cut -d' ' -f2)
    if ros2 pkg executables "$pkg" 2>/dev/null | grep -q "$exe"; then
        pass "$pkg/$exe"
    else
        fail "$pkg/$exe not found"
    fi
done

# ── 5. Print demo commands ───────────────────────────────────────
echo ""
echo "=== Demo commands ==="
echo ""
echo "  Terminal 1 — Simulation:"
echo "    ros2 launch arctos_description simulation.launch.py"
echo ""
echo "  Terminal 2 — Calibration pipeline:"
echo "    ros2 launch arctos_bringup arctos_bringup.launch.py perception_mode:=sim_detection enable_solver:=true"
echo ""
echo "  Terminal 3 — Joint motion demo:"
echo "    ros2 launch arctos_twin joint_motion_demo.launch.py"
echo ""
echo "  Terminal 4 — Monitor topics:"
echo "    ros2 topic list | grep arctos"
echo "    ros2 topic echo /arctos/calibration/solution --once"
echo "    ros2 topic echo /arctos/evaluation/metrics --once"

# ── 6. Live topic check (optional) ──────────────────────────────
if [[ "$1" == "--live" ]]; then
    echo ""
    echo "=== Live topic verification ==="
    TOPICS=(
        /arctos/twin/state
        /arctos/twin/sync_error
        /arctos/perception/reference_frame_pose
        /arctos/calibration/result
        /arctos/calibration/state
        /arctos/calibration/solution
        /arctos/evaluation/metrics
    )
    ACTIVE_TOPICS=$(ros2 topic list 2>/dev/null)
    for topic in "${TOPICS[@]}"; do
        if echo "$ACTIVE_TOPICS" | grep -qx "$topic"; then
            pass "$topic"
        else
            fail "$topic not active"
        fi
    done
fi

# ── Summary ──────────────────────────────────────────────────────
echo ""
echo "=== Summary ==="
TOTAL=$((PASS + FAIL))
echo "  $PASS/$TOTAL passed"
if [ "$FAIL" -gt 0 ]; then
    echo "  $FAIL FAILED"
    exit 1
else
    echo "  All checks passed."
    exit 0
fi
