"""Utility functions for file and directory operations."""

import hashlib
import os
import threading
from collections.abc import Callable
from functools import wraps
from pathlib import Path
from typing import Any, TypeVar

from llama_index.core.llms import LLM

from src.doc_types import DocType

# Type variable for generic function return type
T = TypeVar("T")

# Cache size for drift detection results (configurable)
DRIFT_CACHE_SIZE = 100

# Module-level cache storage and lock for thread-safety
_drift_cache: dict[str, Any] = {}
_cache_lock = threading.Lock()


def find_repo_root(start_path: str) -> str | None:
    """
    Find the repository root by searching for .git directory.

    Args:
        start_path: Path to start searching from.

    Returns:
        Path to repository root, or None if not found.
    """
    current = Path(start_path).resolve()

    # Search up the directory tree
    while current != current.parent:
        if (current / ".git").exists():
            return str(current)
        current = current.parent

    return None


def resolve_output_path(*, doc_type: DocType, module_path: str) -> str:
    """
    Resolve output path for documentation file.

    NOTE: This function does NOT create directories. Call ensure_output_directory()
    before writing to the returned path if needed.

    Args:
        doc_type: Type of documentation being generated.
        module_path: Path to the module directory (or any directory in the repo).

    Returns:
        Absolute path to the output documentation file.

    Raises:
        ValueError: If git root not found for repo-wide doc types.
    """
    if doc_type == DocType.MODULE_README:
        return os.path.join(module_path, "README.md")

    # Find git root for repo-wide docs
    repo_root = find_repo_root(module_path)
    if not repo_root:
        raise ValueError(
            f"Cannot generate {doc_type.value}: not in a git repository. "
            f"Initialize git or use MODULE_README type."
        )

    if doc_type == DocType.PROJECT_README:
        return os.path.join(repo_root, "README.md")

    if doc_type == DocType.STYLE_GUIDE:
        return os.path.join(repo_root, "docs", "style-guide.md")

    raise ValueError(f"Unknown doc type: {doc_type}")


def ensure_output_directory(output_path: str) -> None:
    """
    Ensure the parent directory exists for the output path.

    Args:
        output_path: Full path to the output file.

    Raises:
        PermissionError: If cannot create the directory.
    """
    parent_dir = os.path.dirname(output_path)
    if parent_dir and not os.path.exists(parent_dir):
        try:
            os.makedirs(parent_dir, exist_ok=True)
        except PermissionError as e:
            raise PermissionError(f"Cannot create {parent_dir}: {e}") from e


def _hash_content(content: str) -> str:
    """
    Computes a SHA256 hash of the given content string.

    Used for cache key generation to create deterministic fingerprints of content.

    Args:
        content: The string content to hash.

    Returns:
        A hexadecimal string representation of the SHA256 hash.
    """
    return hashlib.sha256(content.encode()).hexdigest()


def _generate_cache_key(context: str, current_doc: str, llm: LLM) -> str:
    """
    Generates a cache key based on content hashes and LLM model.

    Args:
        context: The code context string.
        current_doc: The current documentation string.
        llm: The LLM client instance.

    Returns:
        A cache key string combining content hashes and model identifier.
    """
    context_hash = _hash_content(context)
    doc_hash = _hash_content(current_doc)
    # Extract model identifier from LLM instance
    llm_model = getattr(llm, "model", "unknown")
    return f"{context_hash}:{doc_hash}:{llm_model}"


def content_based_cache(
    cache_key_fn: Callable[..., str],
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator that caches function results based on a custom cache key.

    This decorator provides thread-safe caching with FIFO eviction when the cache
    reaches its size limit. It's designed for caching expensive operations like
    LLM API calls where the same inputs should return the same outputs.

    Args:
        cache_key_fn: A function that takes the same arguments as the decorated
                     function and returns a cache key string.

    Returns:
        A decorator function that wraps the target function with caching logic.

    Example:
        >>> @content_based_cache(lambda x, y: f"{x}:{y}")
        ... def expensive_function(x: str, y: str) -> str:
        ...     return f"Result: {x} + {y}"
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            # Generate cache key from function arguments
            cache_key = cache_key_fn(*args, **kwargs)

            # Check cache first (with lock for thread-safety)
            with _cache_lock:
                if cache_key in _drift_cache:
                    return _drift_cache[cache_key]

            # Cache miss - call the actual function (outside lock to avoid blocking)
            result = func(*args, **kwargs)

            # Store in cache (with lock and size limit)
            with _cache_lock:
                if len(_drift_cache) >= DRIFT_CACHE_SIZE:
                    # Remove oldest entry (FIFO eviction)
                    # In Python 3.7+, dicts maintain insertion order
                    oldest_key = next(iter(_drift_cache))
                    del _drift_cache[oldest_key]

                _drift_cache[cache_key] = result

            return result

        return wrapper

    return decorator


def clear_drift_cache() -> None:
    """
    Clears the drift detection cache.

    This is useful for testing or when you want to force fresh function calls
    regardless of cache state.
    """
    with _cache_lock:
        _drift_cache.clear()


def get_drift_cache_info() -> dict[str, int]:
    """
    Returns information about the drift detection cache.

    Returns:
        A dictionary with cache statistics (current size and max size).
    """
    with _cache_lock:
        return {"size": len(_drift_cache), "maxsize": DRIFT_CACHE_SIZE}
