try:
    from .features.stats.constants import (  # noqa: F401
        ALLOWED_STATS_PRODUCTS,
        DEFAULT_RUNTIME_PATH_TEMPLATE,
        DEFAULT_SNAPSHOT_PATH_TEMPLATE,
        MAX_RUNTIME_FILE_SIZE,
        MAX_RUNTIME_ID_LENGTH,
        MAX_RUNTIME_LINES,
        SNAPSHOT_FIELDS,
    )
    from .features.stats.errors import StatsStorageError, StatsValidationError
    from .features.stats.path_builder import PathTemplateBuilder
    from .features.stats.service import StatsService, handle_stats
    from .features.stats.validators import validate_runtime_bytes, validate_safe_id
except ImportError:
    from src.features.stats.constants import (  # noqa: F401
        ALLOWED_STATS_PRODUCTS,
        DEFAULT_RUNTIME_PATH_TEMPLATE,
        DEFAULT_SNAPSHOT_PATH_TEMPLATE,
        MAX_RUNTIME_FILE_SIZE,
        MAX_RUNTIME_ID_LENGTH,
        MAX_RUNTIME_LINES,
        SNAPSHOT_FIELDS,
    )
    from src.features.stats.errors import StatsStorageError, StatsValidationError
    from src.features.stats.path_builder import PathTemplateBuilder
    from src.features.stats.service import StatsService, handle_stats
    from src.features.stats.validators import validate_runtime_bytes, validate_safe_id


def build_stats_path(
    template: str,
    allowed_fields: set[str],
    values: dict[str, str],
) -> str:
    return PathTemplateBuilder().build(template, allowed_fields, values)
