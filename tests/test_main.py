import pytest
from unittest.mock import patch
from unittest.mock import MagicMock, patch
from botocore.exceptions import ClientError
from requests import Response

from src.main import (
    handler,
    update_s3_object,
    get_and_update_copilot_teams,
    get_team_history,
)


class TestUpdateS3Object:
    def test_update_s3_object_success(self, caplog):
        s3_client = MagicMock()
        bucket_name = "test-bucket"
        object_name = "test.json"
        data = {"foo": "bar"}

        caplog.set_level("INFO")  # Ensure INFO logs are captured

        update_s3_object(s3_client, bucket_name, object_name, data)

        s3_client.put_object.assert_called_once()
        args, kwargs = s3_client.put_object.call_args
        assert kwargs["Bucket"] == bucket_name
        assert kwargs["Key"] == object_name
        assert kwargs["Body"] == b'{\n    "foo": "bar"\n}'

        assert any("Successfully updated" in record.getMessage() for record in caplog.records)

    def test_update_s3_object_failure(self, caplog):
        s3_client = MagicMock()
        s3_client.put_object.side_effect = ClientError(
            error_response={"Error": {"Code": "500", "Message": "InternalError"}},
            operation_name="PutObject"
        )
        bucket_name = "test-bucket"
        object_name = "test.json"
        data = {"foo": "bar"}

        update_s3_object(s3_client, bucket_name, object_name, data)

        assert s3_client.put_object.called
        assert any("Failed to update" in record.message for record in caplog.records)


class TestGetAndUpdateCopilotTeams:
    @patch("src.main.update_s3_object")
    def test_get_and_update_copilot_teams_single_page(self, mock_update_s3_object):
        s3 = MagicMock()
        gh = MagicMock()
        # Mock response for first page
        mock_response = MagicMock()
        mock_response.links = {}  # No 'last' link, so only one page
        gh.get.return_value = mock_response

        # Patch get_copilot_team_date to return a list of teams
        with patch("src.main.get_copilot_team_date", return_value=[{"name": "team1"}]) as mock_get_team_date:
            result = get_and_update_copilot_teams(s3, gh)
            assert result == [{"name": "team1"}]
            mock_get_team_date.assert_called_once_with(gh, 1)
            mock_update_s3_object.assert_called_once()
            args, kwargs = mock_update_s3_object.call_args
            assert args[1].endswith("copilot-usage-dashboard")
            assert args[2] == "copilot_teams.json"
            assert args[3] == [{"name": "team1"}]

    @patch("src.main.update_s3_object")
    def test_get_and_update_copilot_teams_multiple_pages(self, mock_update_s3_object):
        s3 = MagicMock()
        gh = MagicMock()
        # Mock response with 'last' link for 3 pages
        mock_response = MagicMock()
        mock_response.links = {"last": {"url": "https://api.github.com/orgs/test/teams?page=3"}}
        gh.get.return_value = mock_response

        # Patch get_copilot_team_date to return different teams per page
        with patch("src.main.get_copilot_team_date", side_effect=[
            [{"name": "team1"}],
            [{"name": "team2"}],
            [{"name": "team3"}]
        ]) as mock_get_team_date:
            result = get_and_update_copilot_teams(s3, gh)
            assert result == [{"name": "team1"}, {"name": "team2"}, {"name": "team3"}]
            assert mock_get_team_date.call_count == 3
            mock_update_s3_object.assert_called_once()

    @patch("src.main.update_s3_object")
    def test_get_and_update_copilot_teams_no_teams(self, mock_update_s3_object):
        s3 = MagicMock()
        gh = MagicMock()
        mock_response = MagicMock()
        mock_response.links = {}
        gh.get.return_value = mock_response

        with patch("src.main.get_copilot_team_date", return_value=[]) as mock_get_team_date:
            result = get_and_update_copilot_teams(s3, gh)
            assert result == []
            mock_get_team_date.assert_called_once_with(gh, 1)
            mock_update_s3_object.assert_called_once()
            args, kwargs = mock_update_s3_object.call_args
            assert args[1].endswith("copilot-usage-dashboard")
            assert args[2] == "copilot_teams.json"
            assert args[3] == []


class TestGetTeamHistory:
    def setup_method(self):
        self.org_patch = patch("src.main.org", "test-org")
        self.org_patch.start()
        self.addCleanup = getattr(self, "addCleanup", lambda f: None)

    def teardown_method(self):
        self.org_patch.stop()

    def test_get_team_history_success(self):
        gh = MagicMock()
        mock_response = MagicMock(spec=Response)
        mock_response.json.return_value = [{"date": "2024-01-01", "usage": 5}]
        gh.get.return_value = mock_response


        result = get_team_history(gh, "dev-team", {"since": "2024-01-01"})
        gh.get.assert_called_once_with("/orgs/test-org/team/dev-team/copilot/metrics", params={"since": "2024-01-01"})
        assert result == [{"date": "2024-01-01", "usage": 5}]

    def test_get_team_history_unexpected_response_type(self, caplog):
        gh = MagicMock()
        gh.get.return_value = "not_a_response"


        with caplog.at_level("ERROR"):
            result = get_team_history(gh, "dev-team")
            assert result is None
            assert any("Unexpected response type" in record.getMessage() for record in caplog.records)

    def test_get_team_history_with_no_query_params(self):
        gh = MagicMock()
        mock_response = MagicMock(spec=Response)
        mock_response.json.return_value = []
        gh.get.return_value = mock_response


        result = get_team_history(gh, "dev-team")
        gh.get.assert_called_once_with("/orgs/test-org/team/dev-team/copilot/metrics", params=None)
        assert result == []
