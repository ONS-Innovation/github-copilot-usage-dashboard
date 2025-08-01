import pytest
from unittest.mock import patch

from src.main import (
    handler,
)

class TestHandler:
    def test_handler(self):
        result = handler({}, {})
        assert result == "Github Data logging is now complete."

    # TODO: test each endpoint

class TestGetAccessToken:
    def test_get_access_token_success(self):
        secret_manager_mock = patch("boto3.client").start()
        secret_manager_mock.get_secret_value.return_value = {"SecretString": "mock_pem_contents"}
        with patch("github_api_toolkit.get_token_as_installation", return_value=("mock_token", "mock_other_value")):
            result = get_access_token(secret_manager_mock, "mock_secret_name", "mock_org", "mock_app_client_id")
            assert result == ("mock_token", "mock_other_value")

    def test_get_access_token_secret_not_found(self):
        secret_manager_mock = patch("boto3.client").start()
        secret_manager_mock.get_secret_value.return_value = {"SecretString": ""}
        with pytest.raises(Exception) as excinfo:
            get_access_token(secret_manager_mock, "mock_secret_name", "mock_org", "mock_app_client_id")
        assert (
            "Secret mock_secret_name not found in AWS Secret Manager. Please check your environment variables."
            in str(excinfo.value)
        )

    def test_get_access_token_invalid_token(self):
        secret_manager_mock = patch("boto3.client").start()
        secret_manager_mock.get_secret_value.return_value = {"SecretString": "mock_pem_contents"}
        with patch("github_api_toolkit.get_token_as_installation", return_value="error_message"):
            with pytest.raises(Exception) as excinfo:
                get_access_token(secret_manager_mock, "mock_secret_name", "mock_org", "mock_app_client_id")
            assert "error_message" in str(excinfo.value)