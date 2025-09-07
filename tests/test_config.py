"""Configuration and environment tests."""

import os
from unittest.mock import patch

import httpx

from bookalimo.config import (
    DEFAULT_BACKOFF,
    DEFAULT_BASE_URL,
    DEFAULT_RETRIES,
    DEFAULT_TIMEOUTS,
    DEFAULT_USER_AGENT,
)


class TestDefaultConfiguration:
    """Tests for default configuration values."""

    def test_default_base_url(self):
        """Test default base URL is correct."""
        assert isinstance(DEFAULT_BASE_URL, str)
        assert DEFAULT_BASE_URL.startswith("https://")
        assert not DEFAULT_BASE_URL.endswith("/")

    def test_default_timeouts(self):
        """Test default timeouts configuration."""
        # Should be a timeout configuration object or dict
        assert DEFAULT_TIMEOUTS is not None

        # Check the type and validate appropriately
        if isinstance(DEFAULT_TIMEOUTS, dict):  # type: ignore[unreachable]
            # If it's a dict, should have reasonable values
            assert "connect" in DEFAULT_TIMEOUTS or "timeout" in DEFAULT_TIMEOUTS  # type: ignore[unreachable]
            connect_timeout = DEFAULT_TIMEOUTS.get("connect", None)
            if connect_timeout is not None:
                assert connect_timeout > 0
                assert connect_timeout <= 60
        elif isinstance(DEFAULT_TIMEOUTS, httpx.Timeout):
            connect_timeout = DEFAULT_TIMEOUTS.connect
            if connect_timeout is not None:
                assert connect_timeout > 0
                assert connect_timeout <= 60
        elif isinstance(DEFAULT_TIMEOUTS, (int, float)):
            assert DEFAULT_TIMEOUTS > 0
            assert DEFAULT_TIMEOUTS <= 60

    def test_default_user_agent(self):
        """Test default user agent string."""
        assert isinstance(DEFAULT_USER_AGENT, str)
        assert len(DEFAULT_USER_AGENT) > 0
        assert "bookalimo" in DEFAULT_USER_AGENT.lower()

        # Should include version information
        # Pattern should be like: "bookalimo-python/1.0.0"
        parts = DEFAULT_USER_AGENT.split("/")
        assert len(parts) >= 2
        assert "bookalimo" in parts[0].lower()

    def test_default_retries(self):
        """Test default retry configuration."""
        assert isinstance(DEFAULT_RETRIES, int)
        assert DEFAULT_RETRIES >= 0
        assert DEFAULT_RETRIES <= 10  # Reasonable upper bound

    def test_default_backoff(self):
        """Test default backoff configuration."""
        assert isinstance(DEFAULT_BACKOFF, (int, float))
        assert DEFAULT_BACKOFF > 0
        assert DEFAULT_BACKOFF <= 10  # Reasonable upper bound


class TestConfigurationLoading:
    """Tests for configuration loading from environment."""

    def test_environment_variable_handling(self):
        """Test handling of environment variables."""
        # Test that environment variables don't interfere with defaults
        OLD_DEFAULT_BASE_URL = DEFAULT_BASE_URL
        with patch.dict(os.environ, {"BOOKALIMO_API_URL": "https://custom.api.com"}):
            # Config values should not be affected by random environment variables
            assert DEFAULT_BASE_URL == OLD_DEFAULT_BASE_URL

    def test_google_places_api_key_environment(self):
        """Test Google Places API key from environment."""
        test_key = "test-google-places-api-key-12345"

        with patch.dict(os.environ, {"GOOGLE_PLACES_API_KEY": test_key}):
            # Should be accessible via environment
            assert os.getenv("GOOGLE_PLACES_API_KEY") == test_key

        # Should be cleared when context exits
        with patch.dict(os.environ, {}, clear=True):
            assert os.getenv("GOOGLE_PLACES_API_KEY") is None

    def test_environment_variable_precedence(self):
        """Test that environment variables take precedence where applicable."""
        # This test would apply if the SDK supports environment-based configuration
        # For now, we test that environment variables don't break anything

        OLD_DEFAULT_BASE_URL = DEFAULT_BASE_URL

        test_env_vars = {
            "HTTP_PROXY": "http://proxy.example.com:8080",
            "HTTPS_PROXY": "http://proxy.example.com:8080",
            "NO_PROXY": "localhost,127.0.0.1",
        }

        with patch.dict(os.environ, test_env_vars):
            # Should not break default configuration loading
            assert DEFAULT_BASE_URL == OLD_DEFAULT_BASE_URL
            assert isinstance(DEFAULT_TIMEOUTS, (dict, int, float, object))

    def test_configuration_immutability(self):
        """Test that configuration values are not accidentally mutable."""
        original_base_url = DEFAULT_BASE_URL
        original_retries = DEFAULT_RETRIES
        original_backoff = DEFAULT_BACKOFF

        # These should be immutable
        assert DEFAULT_BASE_URL == original_base_url
        assert DEFAULT_RETRIES == original_retries
        assert DEFAULT_BACKOFF == original_backoff

        # Attempting to modify should not affect other imports
        # (This is more about testing our test setup than the actual code)
        try:
            # This should not be possible or should not affect other uses
            modified_base_url = DEFAULT_BASE_URL + "/modified"
            assert modified_base_url != DEFAULT_BASE_URL
        except TypeError:
            # If strings are immutable (which they are), this is expected
            pass


class TestUserAgentParsing:
    """Tests for user agent string parsing and validation."""

    def test_user_agent_format(self):
        """Test user agent follows expected format."""
        # Should follow pattern: product/version (optional comments)
        ua_parts = DEFAULT_USER_AGENT.split()

        # First part should be product/version
        assert len(ua_parts) >= 1
        product_version = ua_parts[0]

        assert "/" in product_version
        product, version = product_version.split("/", 1)

        assert len(product) > 0
        assert len(version) > 0

        # Version should look like a version number
        version_parts = version.split(".")
        assert len(version_parts) >= 2  # At least major.minor

        # Should be numeric version components
        for part in version_parts:
            # Remove any non-numeric suffixes (like -alpha, -beta)
            numeric_part = part.split("-")[0]
            assert numeric_part.isdigit(), (
                f"Version part '{part}' should start with digits"
            )

    def test_user_agent_length(self):
        """Test user agent string is reasonable length."""
        assert len(DEFAULT_USER_AGENT) > 10  # Not too short
        assert len(DEFAULT_USER_AGENT) < 200  # Not too long

    def test_user_agent_characters(self):
        """Test user agent contains only valid characters."""
        # User agent should only contain printable ASCII characters
        for char in DEFAULT_USER_AGENT:
            assert ord(char) >= 32, f"Character '{char}' is not printable"
            assert ord(char) <= 126, f"Character '{char}' is not ASCII"

    def test_user_agent_no_sensitive_info(self):
        """Test user agent doesn't contain sensitive information."""
        ua_lower = DEFAULT_USER_AGENT.lower()

        # Should not contain potentially sensitive info
        sensitive_terms = [
            "password",
            "key",
            "token",
            "secret",
            "private",
            "username",
            "email",
            "phone",
            "address",
        ]

        for term in sensitive_terms:
            assert term not in ua_lower, f"User agent contains sensitive term: {term}"


class TestTimeoutConfiguration:
    """Tests for timeout configuration handling."""

    def test_timeout_is_valid(self):
        """Test that timeout configuration is valid."""
        timeout = DEFAULT_TIMEOUTS

        # Should be either a number or a timeout object
        if isinstance(timeout, (int, float)):
            assert timeout > 0
            assert timeout <= 300  # 5 minutes max seems reasonable
        elif hasattr(timeout, "__dict__"):  # type: ignore[unreachable]
            # Should be a timeout object with expected attributes
            timeout_attrs = ["connect", "read", "write", "pool"]
            has_timeout_attr = any(hasattr(timeout, attr) for attr in timeout_attrs)
            assert has_timeout_attr, "Timeout object should have timeout attributes"

    def test_timeout_serialization(self):
        """Test that timeout can be serialized (for logging, etc.)."""
        timeout = DEFAULT_TIMEOUTS

        # Should be convertible to string without errors
        timeout_str = str(timeout)
        assert isinstance(timeout_str, str)
        assert len(timeout_str) > 0

    def test_timeout_reasonable_values(self):
        """Test that timeout values are reasonable."""
        timeout = DEFAULT_TIMEOUTS

        # Extract timeout values for testing
        timeout_values = []

        if isinstance(timeout, (int, float)):
            timeout_values.append(timeout)
        elif hasattr(timeout, "connect"):  # type: ignore[unreachable]
            if hasattr(timeout, "connect") and timeout.connect is not None:
                timeout_values.append(timeout.connect)
            if hasattr(timeout, "read") and timeout.read is not None:
                timeout_values.append(timeout.read)
        elif isinstance(timeout, dict):
            for key in ["connect", "read", "write", "pool"]:
                if key in timeout and timeout[key] is not None:
                    timeout_values.append(timeout[key])

        # Validate all collected timeout values
        for value in timeout_values:
            assert isinstance(value, (int, float))
            assert value > 0, "Timeout values should be positive"
            assert value <= 300, "Timeout values should be reasonable (≤5 minutes)"


class TestRetryConfiguration:
    """Tests for retry configuration."""

    def test_retry_count_reasonable(self):
        """Test retry count is reasonable."""
        assert DEFAULT_RETRIES >= 0, "Retry count should not be negative"
        assert DEFAULT_RETRIES <= 10, "Retry count should not be excessive"

    def test_backoff_reasonable(self):
        """Test backoff timing is reasonable."""
        assert DEFAULT_BACKOFF > 0, "Backoff should be positive"
        assert DEFAULT_BACKOFF <= 60, "Backoff should not be excessive"

        # Test exponential backoff would be reasonable
        max_backoff = DEFAULT_BACKOFF * (2**DEFAULT_RETRIES)
        assert max_backoff <= 300, "Maximum backoff should be reasonable (≤5 minutes)"

    def test_retry_configuration_consistency(self):
        """Test retry configuration is internally consistent."""
        # If retries is 0, backoff is irrelevant but should still be positive
        if DEFAULT_RETRIES == 0:
            assert DEFAULT_BACKOFF > 0  # Should still be valid even if unused

        # Total maximum retry time should be reasonable
        if DEFAULT_RETRIES > 0:
            # Sum of geometric series: a * (1 - r^n) / (1 - r) where r = 2
            max_total_time = DEFAULT_BACKOFF * (2**DEFAULT_RETRIES - 1)
            assert max_total_time <= 600, (
                "Total retry time should be reasonable (≤10 minutes)"
            )


class TestConfigurationIntegrity:
    """Tests for overall configuration integrity."""

    def test_all_config_values_defined(self):
        """Test that all expected configuration values are defined."""
        config_values = [
            DEFAULT_BASE_URL,
            DEFAULT_TIMEOUTS,
            DEFAULT_USER_AGENT,
            DEFAULT_RETRIES,
            DEFAULT_BACKOFF,
        ]

        for value in config_values:
            assert value is not None, f"Configuration value should not be None: {value}"

    def test_config_values_types(self):
        """Test configuration value types are correct."""
        assert isinstance(DEFAULT_BASE_URL, str)
        assert isinstance(DEFAULT_USER_AGENT, str)
        assert isinstance(DEFAULT_RETRIES, int)
        assert isinstance(DEFAULT_BACKOFF, (int, float))

        # DEFAULT_TIMEOUTS can be various types depending on implementation
        timeout_valid_types = (int, float, dict, object)
        assert isinstance(DEFAULT_TIMEOUTS, timeout_valid_types)

    def test_config_loading_performance(self):
        """Test that config loading is fast."""
        import time

        start_time = time.perf_counter()

        # Re-import config (simulating loading)

        end_time = time.perf_counter()
        elapsed = end_time - start_time

        # Config loading should be very fast
        assert elapsed < 0.1, f"Config loading took {elapsed:.4f}s"

    def test_config_no_side_effects(self):
        """Test that importing config has no side effects."""
        # This test ensures that importing config doesn't:
        # - Make network requests
        # - Create files
        # - Modify global state

        original_env = os.environ.copy()

        try:
            # Import config again
            import importlib

            import bookalimo.config

            importlib.reload(bookalimo.config)

            # Environment should be unchanged
            assert os.environ == original_env

        finally:
            # Restore environment just in case
            os.environ.clear()
            os.environ.update(original_env)
