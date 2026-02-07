from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class SystemStatus:
    state: str
    updated_at: datetime


@dataclass(frozen=True)
class CameraStatus:
    state: str
    temperature_c: float
    exposure_ms: float
    gain_db: float


class ApiClient:
    """Mock API client that will later map to FastAPI endpoints."""

    def get_system_status(self) -> SystemStatus:
        return SystemStatus(state="Online", updated_at=datetime.utcnow())

    def get_camera_status(self) -> CameraStatus:
        return CameraStatus(
            state="Standby",
            temperature_c=36.4,
            exposure_ms=7.5,
            gain_db=3.0,
        )

    def set_camera_setting(self, name: str, value: float) -> None:
        _ = (name, value)
        return None
