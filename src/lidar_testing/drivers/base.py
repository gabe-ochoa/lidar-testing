from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generator


@dataclass
class ScanPoint:
    quality: int  # signal quality 0-47
    angle: float  # degrees 0-360
    distance: float  # millimeters (0 = invalid/no return)


Scan = list[ScanPoint]


class LidarDriver(ABC):
    @abstractmethod
    def connect(self) -> None: ...

    @abstractmethod
    def disconnect(self) -> None: ...

    @abstractmethod
    def iter_scans(self) -> Generator[Scan, None, None]: ...

    @abstractmethod
    def get_info(self) -> dict: ...
