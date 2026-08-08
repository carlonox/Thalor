# Motor Control Skill

Controls the robot's throttle and steering via the backend REST API.

## Functions

```python
def set_throttle(value: float):
    """Set throttle (0.0 to 1.0)."""
    requests.post(f"{ROBOT_URL}/api/motor/throttle", json={"value": value})

def set_steering(angle: float):
    """Set steering angle (-30° to +30°)."""
    requests.post(f"{ROBOT_URL}/api/motor/steering", json={"angle": angle})
```

## Environment

- `ROBOT_URL` — Backend base URL (e.g. `http://host.docker.internal:5002`)

## Safety

- Never exceed 1.0 throttle without pilot confirmation
- Never execute maneuvers with battery < 20%
