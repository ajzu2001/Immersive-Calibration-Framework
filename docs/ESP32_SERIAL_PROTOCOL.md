# ESP32 Serial Protocol

This document defines the USB serial contract between the future ESP32
sensor acquisition board and the ROS 2 Arctos hardware bridge.

## Transport

- Physical link: ESP32 USB serial.
- Encoding: UTF-8 newline-delimited JSON, one complete JSON object per line.
- Expected baud rate: `921600` baud.
- Target acquisition rate: `100 Hz`.
- Minimum acceptable calibration rate: `50 Hz`.

## Packet Format

Example packet:

```json
{
  "timestamp": 123456789,
  "encoders": [0, 0, 0, 0, 0, 0],
  "limit_min": [false, false, false, false, false, false],
  "limit_max": [false, false, false, false, false, false],
  "imu": {
    "roll": 0.0,
    "pitch": 0.0,
    "yaw": 0.0
  },
  "heartbeat": 42
}
```

## Required Fields

- `timestamp`: ESP32-side monotonic timestamp in microseconds or milliseconds. The unit must remain consistent during a run.
- `encoders`: array of six joint encoder positions in radians, ordered joint 1 through joint 6.
- `limit_min`: array of six booleans for minimum/home-side limit switches.
- `limit_max`: array of six booleans for maximum/end-side limit switches.
- `imu`: object containing `roll`, `pitch`, and `yaw` in radians.
- `heartbeat`: monotonically increasing packet counter, used to detect stalled firmware or dropped packets.

## Validation Rules

The ROS bridge rejects packets when:

- JSON parsing fails.
- A required field is missing.
- `encoders`, `limit_min`, or `limit_max` is not length 6.
- IMU roll, pitch, or yaw is missing or non-numeric.
- `heartbeat` is missing or not numeric.

Rejected packets do not update `/arctos/hardware/joint_sensor_state`.

## Bridge Status

The bridge publishes `/arctos/hardware/bridge_status` as `std_msgs/String`:

- `CONNECTED`: valid packets arrive at `>= 50 Hz`.
- `DEGRADED`: valid packets arrive, but measured rate is `< 50 Hz`.
- `DISCONNECTED`: no valid packet for more than `2 seconds`.

## Error Handling

- Malformed packets are counted and ignored.
- Missing fields are counted and ignored.
- Stale packet timeout changes bridge status to `DISCONNECTED`.
- Low valid packet rate changes bridge status to `DEGRADED`.
- The bridge should continue running after serial disconnects so the ESP32 can be reconnected without restarting the ROS graph.

## Future Extensibility

Future packets may add fields without breaking this contract. Suggested optional fields:

- `encoder_raw`: raw AS5600 counts before radian conversion.
- `imu_raw`: raw accelerometer and gyro values.
- `temperature`: ESP32 or sensor temperature.
- `voltage`: board supply voltage.
- `faults`: firmware-level diagnostic flags.
- `firmware_version`: ESP32 firmware version string.

Consumers must ignore unknown fields unless explicitly upgraded to use them.
