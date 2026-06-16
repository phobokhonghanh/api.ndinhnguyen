try:
    from .core.context import worker_env
except ImportError:
    from src.core.context import worker_env
