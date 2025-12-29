"""Caching utilities for expensive operations like LLM API calls."""

import hashlib
import json
import threading
from collections.abc import Callable
from functools import wraps
from pathlib import Path
from typing import Any, TypeVar

from llama_index.core.llms import LLM

from src.constants import DEFAULT_CACHE_FILE, DRIFT_CACHE_SIZE
from src.records import DocumentationDriftCheck

# Type variable for generic function return type
T = TypeVar("T")


class _DriftCacheStore:
    """
    Thread-safe cache storage for drift detection results.

    This class encapsulates the cache state and provides thread-safe
    operations for managing the cache.
    """

    def __init__(self, max_size: int = DRIFT_CACHE_SIZE):
        """Initialize the cache with a maximum size."""
        self._cache: dict[str, Any] = {}
        self._lock = threading.Lock()
        self._max_size = max_size

    def get(self, key: str) -> Any | None:
        """Get a value from the cache, returns None if not found."""
        with self._lock:
            return self._cache.get(key)

    def set(self, key: str, value: Any) -> None:
        """
        Set a value in the cache, evicting oldest entry if at max size.

        Uses FIFO eviction policy.
        """
        with self._lock:
            if len(self._cache) >= self._max_size:
                # Remove oldest entry (FIFO eviction)
                # In Python 3.7+, dicts maintain insertion order
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]

            self._cache[key] = value

    def clear(self) -> None:
        """Clear all entries from the cache."""
        with self._lock:
            self._cache.clear()

    def get_info(self) -> dict[str, int]:
        """Get cache statistics (size and max size)."""
        with self._lock:
            return {"size": len(self._cache), "maxsize": self._max_size}

    def set_max_size(self, size: int) -> None:
        """Update the maximum cache size."""
        with self._lock:
            self._max_size = size

    def get_all_entries(self) -> dict[str, Any]:
        """Get all cache entries (for saving to disk)."""
        with self._lock:
            return dict(self._cache)

    def load_entries(self, entries: dict[str, Any]) -> None:
        """Load entries into the cache (from disk)."""
        with self._lock:
            for key, value in entries.items():
                self._cache[key] = value


# Module-level cache instance
_drift_cache = _DriftCacheStore()


def _hash_content(content: str | None) -> str:
    """
    Computes a SHA256 hash of the given content string.

    Used for cache key generation to create deterministic fingerprints of content.

    Args:
        content: The string content to hash, or None for empty content.

    Returns:
        A hexadecimal string representation of the SHA256 hash.
    """
    if content is None:
        # Use empty string for None to create a consistent hash
        content = ""
    return hashlib.sha256(content.encode()).hexdigest()


def _generate_cache_key(context: str, current_doc: str | None, llm: LLM) -> str:
    """
    Generates a cache key based on content hashes and LLM model.

    Args:
        context: The code context string.
        current_doc: The current documentation string, or None if no
            documentation exists.
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

            # Check cache first
            cached_value = _drift_cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Cache miss - call the actual function
            result = func(*args, **kwargs)

            # Store in cache
            _drift_cache.set(cache_key, result)

            return result

        return wrapper

    return decorator


def clear_drift_cache() -> None:
    """
    Clears the drift detection cache.

    This is useful for testing or when you want to force fresh function calls
    regardless of cache state.
    """
    _drift_cache.clear()


def get_drift_cache_info() -> dict[str, int]:
    """
    Returns information about the drift detection cache.

    Returns:
        A dictionary with cache statistics (current size and max size).
    """
    return _drift_cache.get_info()


def set_cache_max_size(size: int) -> None:
    """
    Set the maximum cache size from configuration.

    Args:
        size: Maximum number of entries to keep in the cache.
    """
    _drift_cache.set_max_size(size)


def load_drift_cache_from_disk(path: str = DEFAULT_CACHE_FILE) -> None:
    """
    Load drift cache from JSON file if it exists.

    Populates the in-memory cache from a previously saved cache file.
    If the file doesn't exist or is corrupted, silently continues with
    an empty cache.

    Args:
        path: Path to the cache file. Defaults to DEFAULT_CACHE_FILE.
    """
    cache_path = Path(path)
    if not cache_path.exists():
        return

    try:
        data = json.loads(cache_path.read_text())

        # Validate version (for future compatibility)
        if data.get("version") != 1:
            return

        # Load each cache entry and reconstruct DocumentationDriftCheck objects
        entries = {}
        for key, value in data.get("entries", {}).items():
            entries[key] = DocumentationDriftCheck(
                drift_detected=value["drift_detected"],
                rationale=value["rationale"],
            )

        _drift_cache.load_entries(entries)
    except (json.JSONDecodeError, KeyError, ValueError, TypeError):
        # Corrupted cache - silently ignore and start with empty cache
        pass


def save_drift_cache_to_disk(path: str = DEFAULT_CACHE_FILE) -> None:
    """
    Save current drift cache to JSON file.

    Persists the in-memory cache to disk so it can be restored in future runs.
    Creates the cache file and parent directories if they don't exist.

    If save fails (permissions, disk full, etc.), silently continues to avoid
    disrupting the main workflow. The cache is a performance optimization, not
    a critical requirement.

    Args:
        path: Path to the cache file. Defaults to DEFAULT_CACHE_FILE.
    """
    try:
        cache_path = Path(path)

        # Create parent directory if it doesn't exist
        cache_path.parent.mkdir(parents=True, exist_ok=True)

        # Collect cache data
        all_entries = _drift_cache.get_all_entries()
        cache_data = {
            "version": 1,  # For future compatibility
            "entries": {
                key: {
                    "drift_detected": value.drift_detected,
                    "rationale": value.rationale,
                }
                for key, value in all_entries.items()
            },
        }

        # Write atomically to prevent corruption if process is killed
        temp_path = cache_path.with_suffix(".tmp")
        temp_path.write_text(json.dumps(cache_data, indent=2))
        temp_path.replace(cache_path)  # Atomic on POSIX systems

    except OSError:
        # Silently ignore save failures - cache is optional
        # Common failures: disk full, permission denied, read-only filesystem
        pass
