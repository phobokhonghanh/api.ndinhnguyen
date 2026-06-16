try:
    from .core.responses import response
    from .features.bookmarks.service import (
        COLORS,
        build_tree,
        dashboard,
        descendant_ids,
        normalize_bookmark,
        normalize_category,
        remove_bookmark,
        remove_category,
        save_bookmark,
        save_category,
        slugify,
        validate_bookmark,
    )
    from .features.bookmarks import repository
except ImportError:
    from src.core.responses import response
    from src.features.bookmarks.service import (
        COLORS,
        build_tree,
        dashboard,
        descendant_ids,
        normalize_bookmark,
        normalize_category,
        remove_bookmark,
        remove_category,
        save_bookmark,
        save_category,
        slugify,
        validate_bookmark,
    )
    from src.features.bookmarks import repository
