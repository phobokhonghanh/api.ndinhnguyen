import csv
import io
from datetime import datetime

from features.stats.constants import SNAPSHOT_FIELDS


class SnapshotHandler:
    async def write_once(
        self,
        store,
        key: str,
        *,
        snapshot_event_id: str,
        user: str,
        machine_id: str,
        now: datetime,
    ) -> None:
        existing = await store.read_text(key)
        updated = self.append_csv(
            existing,
            snapshot_event_id=snapshot_event_id,
            user=user,
            machine_id=machine_id,
            now=now,
        )
        if updated != existing:
            await store.put(key, updated)

    def append_csv(
        self,
        existing: str,
        *,
        snapshot_event_id: str,
        user: str,
        machine_id: str,
        now: datetime,
    ) -> str:
        if existing.strip():
            rows = list(csv.DictReader(io.StringIO(existing)))
            if any(row.get("snapshot_event_id") == snapshot_event_id for row in rows):
                return existing
        else:
            rows = []

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=SNAPSHOT_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
        writer.writerow(
            {
                "snapshot_event_id": snapshot_event_id,
                "user": user,
                "machine_id": machine_id,
                "created_at_utc": now.isoformat().replace("+00:00", "Z"),
            }
        )
        return output.getvalue()
