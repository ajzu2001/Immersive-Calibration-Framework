"""ESP32 hardware bridge contract MVP.

Reads newline-delimited JSON packets from an ESP32 USB serial link and converts
valid packets into HardwareJointState. For hardware-free testing, it also accepts
identical JSON packets on /arctos/hardware/mock_serial_packet.
"""

import json
import threading
import time
from collections import deque

import rclpy
from rclpy.node import Node

from arctos_interfaces.msg import HardwareJointState
from std_msgs.msg import String


class ESP32BridgeNode(Node):
    """Convert validated ESP32 serial JSON packets into HardwareJointState."""

    JOINT_NAMES = [f'joint_{index + 1}' for index in range(6)]
    REQUIRED_RATE_HZ = 100.0
    MIN_RATE_HZ = 50.0
    DISCONNECT_TIMEOUT_SEC = 2.0

    def __init__(self):
        super().__init__('esp32_bridge_node')
        self.declare_parameter('serial_port', '')
        self.declare_parameter('baud_rate', 921600)
        self.declare_parameter('read_timeout_sec', 0.01)

        self._serial_port = str(self.get_parameter('serial_port').value)
        self._baud_rate = int(self.get_parameter('baud_rate').value)
        self._read_timeout = float(self.get_parameter('read_timeout_sec').value)
        self._serial = None
        self._stop_reader = threading.Event()
        self._valid_packet_times: deque[float] = deque(maxlen=200)
        self._last_valid_packet_time: float | None = None
        self._malformed_packets = 0
        self._missing_field_packets = 0
        self._last_status = 'DISCONNECTED'

        self._state_pub = self.create_publisher(
            HardwareJointState, '/arctos/hardware/joint_sensor_state', 10
        )
        self._status_pub = self.create_publisher(String, '/arctos/hardware/bridge_status', 10)
        self.create_subscription(
            String, '/arctos/hardware/mock_serial_packet', self._on_mock_packet, 10
        )
        self.create_timer(0.2, self._publish_status)

        if self._serial_port:
            self._start_serial_reader()
        else:
            self.get_logger().info(
                'ESP32 bridge started without serial_port; waiting for mock serial packets'
            )

    def _start_serial_reader(self):
        try:
            import serial

            self._serial = serial.Serial(
                self._serial_port,
                self._baud_rate,
                timeout=self._read_timeout,
            )
        except Exception as exc:
            self.get_logger().error(f'Failed to open ESP32 serial port {self._serial_port}: {exc}')
            return

        thread = threading.Thread(target=self._serial_loop, daemon=True)
        thread.start()
        self.get_logger().info(
            f'ESP32 bridge reading {self._serial_port} at {self._baud_rate} baud'
        )

    def _serial_loop(self):
        while not self._stop_reader.is_set() and self._serial is not None:
            try:
                line = self._serial.readline().decode('utf-8', errors='replace').strip()
            except Exception as exc:
                self.get_logger().warn(f'ESP32 serial read error: {exc}')
                time.sleep(0.1)
                continue
            if line:
                self._handle_packet_text(line)

    def _on_mock_packet(self, msg: String):
        self._handle_packet_text(msg.data)

    def _handle_packet_text(self, text: str):
        try:
            packet = json.loads(text)
        except json.JSONDecodeError:
            self._malformed_packets += 1
            self.get_logger().warn('Malformed ESP32 packet ignored')
            return

        try:
            hardware_state = self._packet_to_state(packet)
        except (KeyError, TypeError, ValueError) as exc:
            self._missing_field_packets += 1
            self.get_logger().warn(f'Invalid ESP32 packet ignored: {exc}')
            return

        now = time.monotonic()
        self._last_valid_packet_time = now
        self._valid_packet_times.append(now)
        self._state_pub.publish(hardware_state)

    def _packet_to_state(self, packet: dict) -> HardwareJointState:
        for field in ['timestamp', 'encoders', 'limit_min', 'limit_max', 'imu', 'heartbeat']:
            if field not in packet:
                raise KeyError(f'missing {field}')

        encoders = self._validate_array(packet['encoders'], 'encoders', float)
        limit_min = self._validate_array(packet['limit_min'], 'limit_min', bool)
        limit_max = self._validate_array(packet['limit_max'], 'limit_max', bool)
        imu = packet['imu']
        if not isinstance(imu, dict):
            raise TypeError('imu must be an object')
        roll = float(imu['roll'])
        pitch = float(imu['pitch'])
        yaw = float(imu['yaw'])
        float(packet['timestamp'])
        int(packet['heartbeat'])

        msg = HardwareJointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'esp32_hardware_bridge'
        msg.joint_names = list(self.JOINT_NAMES)
        msg.encoder_positions = encoders
        msg.limit_switch_min = limit_min
        msg.limit_switch_max = limit_max
        msg.imu_roll = roll
        msg.imu_pitch = pitch
        msg.imu_yaw = yaw
        msg.confidence = 0.95
        return msg

    @staticmethod
    def _validate_array(value, name: str, item_type):
        if not isinstance(value, list) or len(value) != 6:
            raise ValueError(f'{name} must be an array of length 6')
        if item_type is bool:
            if not all(isinstance(item, bool) for item in value):
                raise TypeError(f'{name} must contain booleans')
            return list(value)
        return [float(item) for item in value]

    def _publish_status(self):
        status = self._bridge_status()
        msg = String()
        msg.data = status
        self._status_pub.publish(msg)
        if status != self._last_status:
            self.get_logger().info(
                f'ESP32 bridge status={status} rate={self._current_rate_hz():.1f}Hz '
                f'malformed={self._malformed_packets} invalid={self._missing_field_packets}'
            )
            self._last_status = status

    def _bridge_status(self) -> str:
        if self._last_valid_packet_time is None:
            return 'DISCONNECTED'
        if time.monotonic() - self._last_valid_packet_time > self.DISCONNECT_TIMEOUT_SEC:
            return 'DISCONNECTED'
        if self._current_rate_hz() < self.MIN_RATE_HZ:
            return 'DEGRADED'
        return 'CONNECTED'

    def _current_rate_hz(self) -> float:
        if len(self._valid_packet_times) < 2:
            return 0.0
        elapsed = self._valid_packet_times[-1] - self._valid_packet_times[0]
        if elapsed <= 1e-9:
            return 0.0
        return (len(self._valid_packet_times) - 1) / elapsed

    def destroy_node(self):
        self._stop_reader.set()
        if self._serial is not None:
            try:
                self._serial.close()
            except Exception:
                pass
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = ESP32BridgeNode()
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
