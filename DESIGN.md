# Design — lidar-testing

## Goal

Evaluate different lidar hardware for a project that tracks multiple people moving through a space, with the lidar mounted at the center of the room. This repo is the testbed: plug in a lidar, see the raw output, and see tracked people in real time.

## Current hardware

- **RPLIDAR A2M8** — 2D lidar, ~8-10 Hz scan rate, ~400 points per 360° sweep, 115200 baud USB serial. Connected via USB-to-serial adapter (shows up as `/dev/tty.usbserial-*` on macOS).

## Decisions made

### Separate tracking library

The object tracking logic lives in a standalone package (`lidar-tracker`, sibling directory) rather than being embedded in this repo. This was deliberate:

- The tracker is hardware-agnostic — it accepts generic polar points, not `ScanPoint`
- It can be reused in other projects without pulling in FastAPI, rplidar drivers, etc.
- Testing is cleaner — the tracker has its own synthetic test suite independent of real hardware

### Web dashboard over matplotlib

Chose a browser-based visualization (FastAPI + WebSocket + Canvas) instead of a matplotlib real-time plot:

- Easier to share and demo — just open a URL
- Canvas handles thousands of points at 60fps without any framework overhead
- Can overlay tracking info (object IDs, trajectories, velocity arrows) cleanly
- No build tooling — single HTML file with inline JS

### Driver abstraction

All hardware access goes through the `LidarDriver` ABC. The intent is to add more lidar models for comparison without changing the server or frontend. The abstraction is minimal: `connect`, `disconnect`, `iter_scans` (blocking generator), `get_info`.

### Threading model

The lidar driver is synchronous (blocking serial reads). Rather than trying to make it async, we run it in a daemon thread and share data with the async FastAPI handlers through a lock + `asyncio.Event`. This is the simplest correct approach for a single producer (lidar) and multiple consumers (WebSocket clients).

## What the dashboard shows

1. **Raw scan points** — dim gray dots showing the full lidar output (walls, furniture, people, everything)
2. **Tracked objects** — bright colored circles with persistent ID labels, bounding radius, and velocity arrows
3. **Trajectory trails** — faded colored lines showing where each tracked object has been
4. **Background learning status** — the tracker needs ~30 frames (~4 seconds) to learn the static scene before it can detect moving objects
5. **Object sidebar** — per-object stats: distance from sensor, speed, track age

## Future intentions

- **Add more lidar hardware** for side-by-side comparison (different models, price points, scan rates)
- **Tune tracker parameters** per hardware — different lidars have different point densities and noise characteristics
- **Recording and playback** — save raw scans to disk for offline analysis and parameter tuning without needing the hardware plugged in
- **Person counting and zone analytics** — use tracked trajectories to compute occupancy, dwell time, traffic patterns
- **Multi-lidar fusion** — combine data from multiple lidars for better coverage and handling of occlusion
