from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict


@dataclass(frozen=True)
class CameraStatus:
    online: bool
    temperature_c: float
    bitrate_mbps: float
    last_seen: datetime


class ApiClient:
    """Mock API client that simulates backend responses."""

    def fetch_camera_status(self) -> CameraStatus:
        return CameraStatus(
            online=True,
            temperature_c=42.5,
            bitrate_mbps=125.4,
            last_seen=datetime.utcnow(),
        )

    def fetch_camera_settings(self) -> Dict[str, int]:
        return {
            "exposure": 68,
            "gain": 45,
            "gamma": 55,
        }
