try:
    from .features.bookmarks.repository import *  # noqa: F403
except ImportError:
    from src.features.bookmarks.repository import *  # noqa: F403
