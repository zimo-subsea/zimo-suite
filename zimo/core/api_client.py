from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CameraStatus:
    is_streaming: bool
    temperature_c: float
    last_frame: datetime


class ApiClient:
    """Mock API client to emulate HTTP/WebSocket calls."""

    def get_camera_status(self) -> CameraStatus:
        return CameraStatus(
            is_streaming=False,
            temperature_c=38.4,
            last_frame=datetime.utcnow(),
        )

    def get_devices_summary(self) -> dict[str, int]:
        return {"online": 3, "offline": 1}
