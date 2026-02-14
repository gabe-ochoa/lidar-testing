# CLAUDE.md — lidar-testing

## What is this?

A Python project for evaluating and comparing lidar hardware. Currently supports the RPLIDAR A2M8. Provides a real-time web dashboard that visualizes raw scan data and tracked moving objects (people).

Depends on the sibling `lidar-tracker` package (`../lidar-tracker`) for object tracking.

## Project layout

```
src/lidar_testing/
├── drivers/
│   ├── base.py           # LidarDriver ABC, ScanPoint dataclass, Scan type alias
│   └── rplidar_a2.py     # RPLIDAR A2M8 driver (wraps rplidar-roboticia)
├── server.py             # FastAPI app, WebSocket streaming, lidar background thread
└── static/
    └── index.html        # Single-file web dashboard (HTML5 Canvas, no build step)

scripts/
└── scan_test.py          # Quick CLI test — prints 5 scans from hardware
```

## Setup

```bash
uv sync
```

The `lidar-tracker` package is an editable dependency pointing at `../lidar-tracker`. Both must be present.

## Running

Quick hardware test (no web server):
```bash
uv run python scripts/scan_test.py /dev/tty.usbserial-XXXX
```

Web dashboard:
```bash
LIDAR_PORT=/dev/tty.usbserial-XXXX uv run lidar-server
# Open http://localhost:8000
```

Find your serial port with `ls /dev/tty.usb*` after plugging in the lidar.

## Architecture

The server runs a background daemon thread that reads scans from the lidar driver and feeds them through `lidar_tracker.TrackingEngine`. Each scan produces:
- Raw polar points (for full scene visualization)
- Tracked objects with persistent IDs, velocity, and bounding radius
- Trajectory histories for each object

This data is serialized to JSON and pushed to all WebSocket clients. The frontend renders everything on an HTML5 Canvas.

## Adding a new lidar

1. Create a new file in `src/lidar_testing/drivers/` (e.g., `livox_mid360.py`)
2. Implement the `LidarDriver` ABC from `drivers/base.py`:
   - `connect()`, `disconnect()`, `iter_scans()` (generator yielding `list[ScanPoint]`), `get_info()`
3. Update `server.py` to select the driver (currently hardcoded to `RPLidarA2Driver`)

## Key types

- `ScanPoint(quality: int, angle: float, distance: float)` — a single lidar measurement (angle in degrees, distance in mm)
- `Scan = list[ScanPoint]` — one full 360° sweep

## WebSocket payload format

```json
{
  "points": [{"a": 45.0, "d": 3200.5}, ...],
  "objects": [{"id": 1, "x": 1500.0, "y": 2000.0, "vx": 50.0, "vy": -20.0, "radius": 200.0, "age": 42}, ...],
  "trajectories": {"1": [{"x": 1500.0, "y": 2000.0}, ...]},
  "bg_ready": true,
  "frame": 150
}
```

## Dependencies

- `rplidar-roboticia` — RPLIDAR hardware driver (pulls in pyserial)
- `fastapi` + `uvicorn[standard]` — web server and WebSocket
- `lidar-tracker` — object tracking (local editable dependency)

## Style and conventions

- Python 3.11+, src layout, hatchling build system
- No test suite in this repo (the tracking logic is tested in `lidar-tracker`)
- The frontend is a single self-contained HTML file — no npm, no build tooling
- Driver abstraction: all hardware-specific code lives behind the `LidarDriver` ABC
