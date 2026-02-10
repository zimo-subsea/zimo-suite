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

    def __init__(self) -> None:
        self.last_applied_vpu_config: dict[str, object] | None = None
        self.last_force_idr_camera_id: int | None = None

    def get_camera_status(self) -> CameraStatus:
        return CameraStatus(
            is_streaming=False,
            temperature_c=38.4,
            last_frame=datetime.utcnow(),
        )

    def get_devices_summary(self) -> dict[str, int]:
        return {"online": 3, "offline": 1}

    def apply_vpu_configuration(self, config: dict[str, object]) -> None:
        """Mock pipeline update call triggered when user presses Apply."""

        self.last_applied_vpu_config = config

    def force_idr(self, camera_id: int) -> None:
        """Mock immediate encoder command (not persisted in config)."""

        self.last_force_idr_camera_id = camera_id
