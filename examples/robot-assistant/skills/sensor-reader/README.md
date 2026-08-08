# Sensor Reader Skill

Reads all robot sensors (temperature, battery, IMU) via the backend REST API.

## Functions

```python
def read_all():
    """Read all sensors."""
    response = requests.get(f"{ROBOT_URL}/api/sensors")
    return response.json()
```

## Environment

- `ROBOT_URL` — Backend base URL (e.g. `http://host.docker.internal:5002`)

## Usage

```json
{"tool_calls": [
  {"function": {"name": "sensor_reader.read_all", "arguments": "{}"}}
]}
```

Returns: `{"battery": 78, "temperature": 42, "imu": {...}}`
