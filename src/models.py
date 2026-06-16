try:
    from .features.bookmarks.schemas import ApiResponse, BookmarkInput, CategoryInput
except ImportError:
    from src.features.bookmarks.schemas import ApiResponse, BookmarkInput, CategoryInput
