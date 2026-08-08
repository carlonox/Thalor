# Live Calibration Skill

Adjusts trim and dead zones in real time while the robot runs.

## Functions

```python
def trim(axis: str, offset: float):
    """Adjust trim for an axis."""
    requests.post(f"{ROBOT_URL}/api/calibration/trim", json={"axis": axis, "offset": offset})

def dead_zone(value: float):
    """Set dead zone for throttle."""
    requests.post(f"{ROBOT_URL}/api/calibration/dead_zone", json={"value": value})
```

## Environment

- `ROBOT_URL` — Backend base URL (e.g. `http://host.docker.internal:5002`)

## Memory

Save calibration values that worked to Mnemosyne with `scope: global` so they
persist across sessions.
