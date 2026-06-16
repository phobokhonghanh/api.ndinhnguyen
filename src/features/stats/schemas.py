from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True)
class StatsCommand:
    product: str
    machine_id: str
    snapshot: bool
    runtime: bool
    user: str | None
    snapshot_event_id: str | None
    batch_id: str | None
    file: Any | None
    now: datetime | None = None

    @property
    def current_time(self) -> datetime:
        return self.now or datetime.now(UTC)
