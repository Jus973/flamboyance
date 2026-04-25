"""Input validation utilities for Flamboyance.

Provides validation functions for URLs, personas, and other inputs
to prevent security issues and improve error messages.
"""

from __future__ import annotations

import re
from urllib.parse import urlparse

ALLOWED_URL_SCHEMES = frozenset({"http", "https"})

DANGEROUS_URL_PATTERNS = [
    r"^javascript:",
    r"^data:",
    r"^file:",
    r"^ftp:",
    r"^mailto:",
    r"^tel:",
]


class ValidationError(ValueError):
    """Raised when input validation fails."""

    pass


def validate_url(url: str, allow_localhost: bool = True) -> str:
    """Validate and normalize a URL for safe navigation.

    Args:
        url: The URL to validate.
        allow_localhost: Whether to allow localhost URLs (default True).

    Returns:
        The validated and normalized URL.

    Raises:
        ValidationError: If the URL is invalid or uses a disallowed scheme.
    """
    if not url:
        raise ValidationError("URL cannot be empty")

    if not isinstance(url, str):
        raise ValidationError(f"URL must be a string, got {type(url).__name__}")

    url = url.strip()

    for pattern in DANGEROUS_URL_PATTERNS:
        if re.match(pattern, url, re.IGNORECASE):
            raise ValidationError(f"URL scheme not allowed: {url[:20]}...")

    try:
        parsed = urlparse(url)
    except Exception as e:
        raise ValidationError(f"Invalid URL format: {e}") from e

    if not parsed.scheme:
        raise ValidationError(f"URL must include scheme (http:// or https://): {url[:50]}")

    if parsed.scheme.lower() not in ALLOWED_URL_SCHEMES:
        raise ValidationError(f"URL scheme '{parsed.scheme}' not allowed. Use http:// or https://")

    if not parsed.netloc:
        raise ValidationError(f"URL must include a host: {url[:50]}")

    host = parsed.hostname or ""

    if not allow_localhost:
        localhost_patterns = ["localhost", "127.0.0.1", "::1", "0.0.0.0"]
        if host.lower() in localhost_patterns:
            raise ValidationError(f"Localhost URLs not allowed: {url[:50]}")

    if _is_private_ip(host) and not allow_localhost:
        raise ValidationError(f"Private IP addresses not allowed: {url[:50]}")

    return url


def _is_private_ip(host: str) -> bool:
    """Check if a hostname is a private IP address."""
    try:
        parts = host.split(".")
        if len(parts) != 4:
            return False

        octets = [int(p) for p in parts]
        if not all(0 <= o <= 255 for o in octets):
            return False

        if octets[0] == 10:
            return True
        if octets[0] == 172 and 16 <= octets[1] <= 31:
            return True
        if octets[0] == 192 and octets[1] == 168:
            return True
        return octets[0] == 127
    except (ValueError, AttributeError):
        return False


def validate_timeout(timeout: float | int, min_val: float = 1.0, max_val: float = 3600.0) -> float:
    """Validate a timeout value.

    Args:
        timeout: The timeout value in seconds.
        min_val: Minimum allowed timeout (default 1 second).
        max_val: Maximum allowed timeout (default 1 hour).

    Returns:
        The validated timeout as a float.

    Raises:
        ValidationError: If the timeout is invalid.
    """
    try:
        timeout_f = float(timeout)
    except (TypeError, ValueError) as e:
        raise ValidationError(f"Timeout must be a number, got {type(timeout).__name__}") from e

    if timeout_f < min_val:
        raise ValidationError(f"Timeout must be at least {min_val}s, got {timeout_f}s")

    if timeout_f > max_val:
        raise ValidationError(f"Timeout must be at most {max_val}s, got {timeout_f}s")

    return timeout_f


def validate_personas(
    persona_names: list[str] | None,
    available: dict[str, object],
) -> list[str]:
    """Validate a list of persona names.

    Args:
        persona_names: List of persona names to validate, or None for all.
        available: Dictionary of available persona names to persona objects.

    Returns:
        List of validated persona names.

    Raises:
        ValidationError: If any persona name is invalid.
    """
    if persona_names is None:
        return list(available.keys())

    if not isinstance(persona_names, list):
        raise ValidationError(f"personas must be a list, got {type(persona_names).__name__}")

    invalid = [name for name in persona_names if name not in available]
    if invalid:
        raise ValidationError(
            f"Unknown persona(s): {', '.join(invalid)}. "
            f"Available: {', '.join(sorted(available.keys()))}"
        )

    return persona_names
