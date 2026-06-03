"""Automated experiment evidence recorder for calibration compensation trials.

The runner records the unified metrics vector and saves dissertation evidence as
CSV plus plots once the requested number of samples has been collected.
"""

import csv
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import rclpy
from rclpy.node import Node

from std_msgs.msg import Float64MultiArray

from arctos_evaluation.plot_results import generate_plots


METRIC_COLUMNS = [
    'timestamp',
    'mean_twin_error',
    'max_twin_error',
    'rms_twin_error',
    'calibration_latest',
    'calibration_best',
    'calibration_average',
    'correction_magnitude',
    'raw_error',
    'compensated_error',
    'improvement_percent',
]


class ExperimentRunnerNode(Node):
    """Record a fixed number of metrics samples and export evidence files."""

    def __init__(self):
        super().__init__('experiment_runner_node')

        self.declare_parameter('trial_count', 50)
        self.declare_parameter(
            'output_directory',
            '~/Immersive-Calibration-Framework/software/arctos_jazzy_ws/results',
        )
        self.declare_parameter('experiment_name', 'calibration_compensation_trial')
        self.declare_parameter('framework_version', 'dissertation-framework-v12')
        self.declare_parameter('perception_mode', 'unknown')

        self._trial_count = int(self.get_parameter('trial_count').value)
        output_directory = str(self.get_parameter('output_directory').value)
        self._output_directory = Path(output_directory).expanduser()
        self._experiment_name = str(self.get_parameter('experiment_name').value)
        self._framework_version = str(self.get_parameter('framework_version').value)
        self._perception_mode = str(self.get_parameter('perception_mode').value)
        self._rows: list[dict[str, Any]] = []
        self._saved = False

        self.create_subscription(
            Float64MultiArray,
            '/arctos/evaluation/metrics',
            self._on_metrics,
            10,
        )

        self.get_logger().info(
            'ExperimentRunnerNode started - recording '
            f'{self._trial_count} samples to {self._output_directory}'
        )

    def _on_metrics(self, msg: Float64MultiArray):
        if self._saved:
            return
        if len(msg.data) < 10:
            self.get_logger().warn(
                f'Ignoring metrics sample with {len(msg.data)} values; expected at least 10'
            )
            return

        if msg.data[7] <= 0.0 or msg.data[8] <= 0.0:
            return

        stamp = self.get_clock().now().nanoseconds / 1e9
        row = {
            'timestamp': stamp,
            'mean_twin_error': msg.data[0],
            'max_twin_error': msg.data[1],
            'rms_twin_error': msg.data[2],
            'calibration_latest': msg.data[3],
            'calibration_best': msg.data[4],
            'calibration_average': msg.data[5],
            'correction_magnitude': msg.data[6],
            'raw_error': msg.data[7],
            'compensated_error': msg.data[8],
            'improvement_percent': msg.data[9],
        }
        self._rows.append(row)

        if len(self._rows) % 10 == 0 or len(self._rows) == self._trial_count:
            self.get_logger().info(
                f'Recorded {len(self._rows)}/{self._trial_count} experiment samples'
            )

        if len(self._rows) >= self._trial_count:
            self._save_results()

    def _save_results(self):
        self._saved = True
        self._output_directory.mkdir(parents=True, exist_ok=True)
        csv_path = self._output_directory / f'{self._experiment_name}_results.csv'

        with csv_path.open('w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=METRIC_COLUMNS)
            writer.writeheader()
            writer.writerows(self._rows)

        self.get_logger().info(f'Saved experiment CSV: {csv_path}')
        metadata_path = self._write_metadata(csv_path)
        self.get_logger().info(f'Saved experiment metadata: {metadata_path}')

        try:
            plot_paths = generate_plots(csv_path)
        except Exception as exc:  # Keep the CSV even if plotting dependencies fail.
            self.get_logger().error(f'Failed to generate plots from {csv_path}: {exc}')
            return

        for plot_path in plot_paths:
            self.get_logger().info(f'Saved experiment plot: {plot_path}')

    def _write_metadata(self, csv_path: Path) -> Path:
        metadata_path = csv_path.parent / 'experiment_metadata.json'
        metadata = {
            'framework_version': self._framework_version,
            'git_commit': self._git_commit(),
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'perception_mode': self._perception_mode,
            'trial_count': self._trial_count,
            'experiment_name': self._experiment_name,
        }
        with metadata_path.open('w') as f:
            json.dump(metadata, f, indent=2)
            f.write('\n')
        return metadata_path

    def _git_commit(self) -> str:
        try:
            return subprocess.check_output(
                ['git', 'rev-parse', 'HEAD'],
                cwd=Path(__file__).resolve().parents[3],
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
        except Exception:
            return 'unknown'


def main(args=None):
    rclpy.init(args=args)
    node = ExperimentRunnerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        try:
            if rclpy.ok():
                rclpy.shutdown()
        except rclpy._rclpy_pybind11.RCLError:
            pass


if __name__ == '__main__':
    main()
