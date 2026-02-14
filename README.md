# lidar-testing

A real-time web dashboard for evaluating lidar hardware. Visualizes raw scan data and tracked moving objects (people) using a browser-based canvas UI.

Currently supports the **RPLIDAR A2M8**. Designed to be extended with additional lidar models for side-by-side comparison.

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- The sibling [`lidar-tracker`](https://github.com/gabe-ochoa/lidar-tracker) package cloned at `../lidar-tracker`
- A supported lidar device connected via USB

## Setup

Clone both repos side by side:

```bash
git clone https://github.com/gabe-ochoa/lidar-testing.git
git clone https://github.com/gabe-ochoa/lidar-tracker.git
```

Install dependencies:

```bash
cd lidar-testing
uv sync
```

This installs `lidar-tracker` as an editable dependency from the sibling directory.

## Usage

### Find your serial port

Plug in the lidar and find the port:

```bash
# macOS
ls /dev/tty.usb*

# Linux
ls /dev/ttyUSB*
```

### Run the web dashboard

```bash
LIDAR_PORT=/dev/tty.usbserial-XXXX uv run lidar-server
```

Open http://localhost:8000 in a browser.

The dashboard shows:
- **Raw scan points** — full lidar output (walls, furniture, people)
- **Tracked objects** — colored circles with persistent IDs, velocity arrows, and bounding radius
- **Trajectory trails** — path history for each tracked object
- **Object sidebar** — per-object stats (distance, speed, track age)

The tracker needs ~30 frames (~4 seconds) to learn the static background before it starts detecting moving objects.

### Quick hardware test (no web server)

```bash
uv run python scripts/scan_test.py /dev/tty.usbserial-XXXX
```

Prints 5 raw scans to the terminal for verifying hardware connectivity.

## Project structure

```
src/lidar_testing/
├── drivers/
│   ├── base.py           # LidarDriver ABC, ScanPoint dataclass
│   └── rplidar_a2.py     # RPLIDAR A2M8 driver
├── server.py             # FastAPI app, WebSocket streaming
└── static/
    └── index.html        # Web dashboard (HTML5 Canvas, no build step)

scripts/
└── scan_test.py          # CLI hardware test
```

## WebSocket API

The server streams JSON frames over WebSocket at `ws://localhost:8000/ws`:

```json
{
  "points": [{"a": 45.0, "d": 3200.5}],
  "objects": [{"id": 1, "x": 1500.0, "y": 2000.0, "vx": 50.0, "vy": -20.0, "radius": 200.0, "age": 42}],
  "trajectories": {"1": [{"x": 1500.0, "y": 2000.0}]},
  "bg_ready": true,
  "frame": 150
}
```

| Field | Description |
|-------|-------------|
| `points` | Raw polar scan data. `a` = angle (degrees), `d` = distance (mm) |
| `objects` | Tracked moving objects with position, velocity, bounding radius, and track age (frames) |
| `trajectories` | Position history keyed by object ID |
| `bg_ready` | Whether the background model has been learned |
| `frame` | Frame counter |

## Adding a new lidar driver

1. Create a new file in `src/lidar_testing/drivers/`
2. Implement the `LidarDriver` ABC from `drivers/base.py`:
   - `connect()` — initialize the hardware connection
   - `disconnect()` — clean up
   - `iter_scans()` — generator yielding `list[ScanPoint]` (one list per 360° sweep)
   - `get_info()` — return device metadata
3. Update `server.py` to select the new driver

## License

MIT
