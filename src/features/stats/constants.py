ALLOWED_STATS_PRODUCTS = {"autohdr"}
MAX_RUNTIME_FILE_SIZE = 256 * 1024
MAX_RUNTIME_LINES = 10_000
MAX_RUNTIME_ID_LENGTH = 128

DEFAULT_SNAPSHOT_PATH_TEMPLATE = (
    "lakehouse-raw/{product}/snapshot/loaddate={yyyymmdd}/{machine_id}.csv"
)
DEFAULT_RUNTIME_PATH_TEMPLATE = (
    "lakehouse-raw/{product}/runtime/loaddate={yyyymmdd}/{machine_id}_{batch_id}.jsonl"
)

SNAPSHOT_FIELDS = ["snapshot_event_id", "user", "machine_id", "created_at_utc"]
