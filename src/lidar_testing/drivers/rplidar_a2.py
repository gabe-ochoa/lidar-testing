from __future__ import annotations

import logging
from typing import Generator

from rplidar import RPLidar

from .base import LidarDriver, Scan, ScanPoint

logger = logging.getLogger(__name__)


class RPLidarA2Driver(LidarDriver):
    def __init__(self, port: str = "/dev/tty.usbserial-0001", baudrate: int = 115200):
        self._port = port
        self._baudrate = baudrate
        self._lidar: RPLidar | None = None

    def connect(self) -> None:
        self._lidar = RPLidar(self._port, baudrate=self._baudrate)
        info = self._lidar.get_info()
        health = self._lidar.get_health()
        logger.info("Connected to RPLidar: %s", info)
        logger.info("Health: %s", health)

    def disconnect(self) -> None:
        if self._lidar:
            self._lidar.stop()
            self._lidar.stop_motor()
            self._lidar.disconnect()
            self._lidar = None

    def iter_scans(self) -> Generator[Scan, None, None]:
        assert self._lidar is not None, "Call connect() first"
        for raw_scan in self._lidar.iter_scans():
            yield [
                ScanPoint(quality=q, angle=a, distance=d)
                for q, a, d in raw_scan
            ]

    def get_info(self) -> dict:
        assert self._lidar is not None, "Call connect() first"
        return self._lidar.get_info()
