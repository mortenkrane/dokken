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

# Module-level cache storage and lock for thread-safety
_drift_cache: dict[str, Any] = {}
_cache_lock = threading.Lock()


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

        with _cache_lock:
            # Load each cache entry and reconstruct DocumentationDriftCheck objects
            for key, value in data.get("entries", {}).items():
                _drift_cache[key] = DocumentationDriftCheck(
                    drift_detected=value["drift_detected"],
                    rationale=value["rationale"],
                )
    except (json.JSONDecodeError, KeyError, ValueError, TypeError):
        # Corrupted cache - silently ignore and start with empty cache
        pass


def save_drift_cache_to_disk(path: str = DEFAULT_CACHE_FILE) -> None:
    """
    Save current drift cache to JSON file.

    Persists the in-memory cache to disk so it can be restored in future runs.
    Creates the cache file if it doesn't exist.

    Args:
        path: Path to the cache file. Defaults to DEFAULT_CACHE_FILE.
    """
    with _cache_lock:
        cache_data = {
            "version": 1,  # For future compatibility
            "entries": {
                key: {
                    "drift_detected": value.drift_detected,
                    "rationale": value.rationale,
                }
                for key, value in _drift_cache.items()
            },
        }

    Path(path).write_text(json.dumps(cache_data, indent=2))
