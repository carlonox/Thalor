# Robot Assistant Example

A **conceptual example** showing how Thalor's architecture applies to a physical robot (AWS DeepRacer).

> **Note:** This is an architectural pattern, not a turnkey deployment. It demonstrates
> how to integrate hardware, voice control, and live calibration with Thalor. You'll need
> your own robot hardware and firmware to run this.

## Overview

This example demonstrates:
- **Hardware integration** — Controlling motors and reading sensors
- **Voice control** — STT/TTS for hands-free operation
- **Live calibration** — Real-time tuning of control parameters
- **Telemetry logging** — Recording lap times and performance metrics
- **Firmware management** — Updating ESP32-S3 firmware

## Architecture

```
┌─────────────────┐
│   DeepRacer     │
│   (Physical)    │
└────────┬────────┘
         │ Serial/WiFi
         ▼
┌─────────────────┐
│  ESP32-S3       │
│  (Firmware)     │
└────────┬────────┘
         │ HTTP REST API
         ▼
┌─────────────────┐
│  Backend        │
│  (Node.js)      │
└────────┬────────┘
         │ MCP Server
         ▼
┌─────────────────┐
│  Thalor Agent   │
│  (This example) │
└─────────────────┘
```

## Components

### Backend (Node.js)

The backend bridges the physical robot with the agent:
- Exposes REST API for motor control
- Reads sensor data (temperature, battery, IMU)
- Handles firmware updates
- Streams telemetry to agent

### Firmware (ESP32-S3)

The firmware runs on the robot:
- Controls motors (throttle, steering)
- Reads sensors (gyroscope, accelerometer)
- Manages power (battery monitoring)
- Communicates via WiFi

### Agent Skills

Custom skills for robot control:
- `motor-control` — Set throttle and steering
- `sensor-reader` — Read all sensors
- `live-calibration` — Adjust trim and dead zones

## Setup

### 1. Clone this example

```bash
cp -r examples/robot-assistant my-robot/
cd my-robot
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your robot's IP and credentials
```

### 3. Start the stack

```bash
# Backend is conceptual — implement your own for your specific hardware
# See docker-compose.yml (commented) for the intended architecture

# Start agent
docker compose up -d
```

### 4. Access dashboard

Open `http://localhost:9999` and start controlling your robot.

## Usage Examples

### Voice Command: "Start autonomous mode"

**User:** Start autonomous mode

**Agent:**
```json
{"tool_calls": [
  {"function": {"name": "motor_control.set_autonomous", "arguments": "{\"enabled\": true}"}}
]}
```

**Tool result:** Autonomous mode enabled. Steering by vision model.

**Agent:** Autonomous mode enabled. The robot will now follow the track using the vision model. Say "stop" to disable. `[mood: focused]`

### Voice Command: "What's the battery level?"

**User:** What's the battery level?

**Agent:**
```json
{"tool_calls": [
  {"function": {"name": "sensor_reader.read_all", "arguments": "{}"}}
]}
```

**Tool result:** `{"battery": 78, "temperature": 42, "imu": {...}}`

**Agent:** Battery at 78% (3.9V per cell), temperature 42°C. You have about 15 minutes of runtime left. `[mood: neutral]`

### Voice Command: "Increase throttle dead zone to 0.15"

**User:** Increase throttle dead zone to 0.15

**Agent:**
```json
{"tool_calls": [
  {"function": {"name": "live_calibration.dead_zone", "arguments": "{\"value\": 0.15}"}}
]}
```

**Tool result:** Dead zone updated to 0.15. Applied to throttle axis.

**Agent:** Dead zone increased to 0.15. This should reduce twitchy acceleration at low speeds. Saving to memory for future sessions. `[mood: focused]`

```json
{"tool_calls": [
  {"function": {"name": "mnemosyne_remember", "arguments": "{\"content\": \"Robot throttle dead zone set to 0.15 on 2026-08-08. Reduced twitchy acceleration.\", \"importance\": 0.6, \"scope\": \"global\"}"}}
]}
```

## Custom Skills

### motor-control

```python
def set_throttle(value: float):
    """Set throttle (0.0 to 1.0)."""
    requests.post(f"{ROBOT_URL}/api/motor/throttle", json={"value": value})

def set_steering(angle: float):
    """Set steering angle (-30° to +30°)."""
    requests.post(f"{ROBOT_URL}/api/motor/steering", json={"angle": angle})
```

### sensor-reader

```python
def read_all():
    """Read all sensors."""
    response = requests.get(f"{ROBOT_URL}/api/sensors")
    return response.json()
```

### live-calibration

```python
def trim(axis: str, offset: float):
    """Adjust trim for an axis."""
    requests.post(f"{ROBOT_URL}/api/calibration/trim", json={"axis": axis, "offset": offset})

def dead_zone(value: float):
    """Set dead zone for throttle."""
    requests.post(f"{ROBOT_URL}/api/calibration/dead_zone", json={"value": value})
```

## Telemetry Logging

The agent automatically logs:
- Lap times
- Best performance
- Calibration changes
- Error events

Stored in Mnemosyne with `scope: global` for cross-session analysis.

## Troubleshooting

### Robot not responding

1. Check robot power (battery level)
2. Verify WiFi connection
3. Ping robot IP: `ping 192.168.1.100`
4. Check backend logs: `docker logs thalor-backend`

### High latency

1. Check WiFi signal strength
2. Reduce video streaming quality
3. Use wired Ethernet if possible

## License

MIT
