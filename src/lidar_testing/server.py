from __future__ import annotations

import asyncio
import json
import logging
import os
import threading
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse

from lidar_tracker import TrackingEngine

from .drivers.rplidar_a2 import RPLidarA2Driver

logger = logging.getLogger(__name__)

_latest_frame: dict = {}
_scan_lock = threading.Lock()
_new_scan = asyncio.Event()


def _lidar_thread(port: str, loop: asyncio.AbstractEventLoop) -> None:
    driver = RPLidarA2Driver(port=port)
    engine = TrackingEngine()

    try:
        driver.connect()
        logger.info("Lidar thread started on port %s", port)
        for scan in driver.iter_scans():
            polar = [(p.angle, p.distance) for p in scan if p.distance > 0]
            frame = engine.process_scan(polar)

            raw_points = [
                {"a": round(p.angle, 2), "d": round(p.distance, 1)}
                for p in scan
                if p.distance > 0
            ]

            objects = [
                {
                    "id": obj.object_id,
                    "x": round(obj.centroid.x, 1),
                    "y": round(obj.centroid.y, 1),
                    "vx": round(obj.velocity.x, 1),
                    "vy": round(obj.velocity.y, 1),
                    "radius": round(obj.bounding_radius_mm, 1),
                    "age": obj.age,
                }
                for obj in frame.objects
            ]

            trajectories = {}
            for obj in frame.objects:
                traj = engine.get_trajectory(obj.object_id)
                trajectories[obj.object_id] = [
                    {"x": round(tp.x, 1), "y": round(tp.y, 1)}
                    for tp in traj[-200:]  # last 200 points
                ]

            payload = {
                "points": raw_points,
                "objects": objects,
                "trajectories": trajectories,
                "bg_ready": engine.background_ready,
                "frame": frame.frame_number,
            }

            with _scan_lock:
                global _latest_frame
                _latest_frame = payload
            loop.call_soon_threadsafe(_new_scan.set)
    except Exception:
        logger.exception("Lidar thread error")
    finally:
        driver.disconnect()
        logger.info("Lidar thread stopped")


@asynccontextmanager
async def lifespan(app: FastAPI):
    port = os.environ.get("LIDAR_PORT", "/dev/tty.usbserial-0001")
    loop = asyncio.get_running_loop()
    t = threading.Thread(target=_lidar_thread, args=(port, loop), daemon=True)
    t.start()
    yield


app = FastAPI(lifespan=lifespan)

STATIC_DIR = Path(__file__).parent / "static"


@app.get("/")
async def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            await _new_scan.wait()
            _new_scan.clear()
            with _scan_lock:
                data = _latest_frame
            await ws.send_text(json.dumps(data))
    except WebSocketDisconnect:
        pass


def main():
    import uvicorn

    logging.basicConfig(level=logging.INFO)
    uvicorn.run(app, host="0.0.0.0", port=8000)
