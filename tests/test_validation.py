"""Tests for agents.validation module."""

import pytest

from agents.validation import (
    ValidationError,
    _is_private_ip,
    validate_personas,
    validate_timeout,
    validate_url,
)


class TestValidateUrl:
    def test_valid_http_url(self) -> None:
        url = validate_url("http://example.com")
        assert url == "http://example.com"

    def test_valid_https_url(self) -> None:
        url = validate_url("https://example.com/path?query=1")
        assert url == "https://example.com/path?query=1"

    def test_valid_localhost(self) -> None:
        url = validate_url("http://localhost:3000", allow_localhost=True)
        assert url == "http://localhost:3000"

    def test_rejects_localhost_when_disabled(self) -> None:
        with pytest.raises(ValidationError, match="Localhost"):
            validate_url("http://localhost:3000", allow_localhost=False)

    def test_rejects_empty_url(self) -> None:
        with pytest.raises(ValidationError, match="empty"):
            validate_url("")

    def test_rejects_javascript_url(self) -> None:
        with pytest.raises(ValidationError, match="not allowed"):
            validate_url("javascript:alert(1)")

    def test_rejects_data_url(self) -> None:
        with pytest.raises(ValidationError, match="not allowed"):
            validate_url("data:text/html,<script>alert(1)</script>")

    def test_rejects_file_url(self) -> None:
        with pytest.raises(ValidationError, match="not allowed"):
            validate_url("file:///etc/passwd")

    def test_rejects_ftp_url(self) -> None:
        with pytest.raises(ValidationError, match="not allowed"):
            validate_url("ftp://example.com/file")

    def test_rejects_url_without_scheme(self) -> None:
        with pytest.raises(ValidationError, match="scheme"):
            validate_url("example.com")

    def test_rejects_url_without_host(self) -> None:
        with pytest.raises(ValidationError, match="host"):
            validate_url("http://")

    def test_strips_whitespace(self) -> None:
        url = validate_url("  http://example.com  ")
        assert url == "http://example.com"

    def test_rejects_non_string(self) -> None:
        with pytest.raises(ValidationError, match="string"):
            validate_url(123)

    def test_rejects_private_ip_when_localhost_disabled(self) -> None:
        with pytest.raises(ValidationError, match="Private IP"):
            validate_url("http://192.168.1.1", allow_localhost=False)

    def test_allows_private_ip_when_localhost_enabled(self) -> None:
        url = validate_url("http://192.168.1.1", allow_localhost=True)
        assert url == "http://192.168.1.1"


class TestIsPrivateIp:
    def test_class_a_private(self) -> None:
        assert _is_private_ip("10.0.0.1") is True
        assert _is_private_ip("10.255.255.255") is True

    def test_class_b_private(self) -> None:
        assert _is_private_ip("172.16.0.1") is True
        assert _is_private_ip("172.31.255.255") is True
        assert _is_private_ip("172.15.0.1") is False
        assert _is_private_ip("172.32.0.1") is False

    def test_class_c_private(self) -> None:
        assert _is_private_ip("192.168.0.1") is True
        assert _is_private_ip("192.168.255.255") is True

    def test_loopback(self) -> None:
        assert _is_private_ip("127.0.0.1") is True
        assert _is_private_ip("127.0.0.255") is True

    def test_public_ip(self) -> None:
        assert _is_private_ip("8.8.8.8") is False
        assert _is_private_ip("1.1.1.1") is False

    def test_invalid_ip(self) -> None:
        assert _is_private_ip("not-an-ip") is False
        assert _is_private_ip("256.0.0.1") is False
        assert _is_private_ip("") is False


class TestValidateTimeout:
    def test_valid_timeout(self) -> None:
        assert validate_timeout(60) == 60.0
        assert validate_timeout(30.5) == 30.5

    def test_string_number(self) -> None:
        assert validate_timeout("60") == 60.0

    def test_rejects_too_small(self) -> None:
        with pytest.raises(ValidationError, match="at least"):
            validate_timeout(0.5)

    def test_rejects_too_large(self) -> None:
        with pytest.raises(ValidationError, match="at most"):
            validate_timeout(7200)

    def test_rejects_non_numeric(self) -> None:
        with pytest.raises(ValidationError, match="number"):
            validate_timeout("not a number")

    def test_custom_bounds(self) -> None:
        assert validate_timeout(0.5, min_val=0.1, max_val=1.0) == 0.5
        with pytest.raises(ValidationError):
            validate_timeout(2.0, min_val=0.1, max_val=1.0)


class TestValidatePersonas:
    def test_none_returns_all(self) -> None:
        available = {"persona1": object(), "persona2": object()}
        result = validate_personas(None, available)
        assert set(result) == {"persona1", "persona2"}

    def test_valid_personas(self) -> None:
        available = {"persona1": object(), "persona2": object(), "persona3": object()}
        result = validate_personas(["persona1", "persona3"], available)
        assert result == ["persona1", "persona3"]

    def test_rejects_unknown_persona(self) -> None:
        available = {"persona1": object(), "persona2": object()}
        with pytest.raises(ValidationError, match="Unknown"):
            validate_personas(["persona1", "unknown"], available)

    def test_rejects_non_list(self) -> None:
        available = {"persona1": object()}
        with pytest.raises(ValidationError, match="list"):
            validate_personas("persona1", available)

    def test_error_shows_available_personas(self) -> None:
        available = {"p1": object(), "p2": object()}
        with pytest.raises(ValidationError) as exc_info:
            validate_personas(["unknown"], available)
        assert "p1" in str(exc_info.value)
        assert "p2" in str(exc_info.value)
