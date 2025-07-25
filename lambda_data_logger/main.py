import json
import logging
import os

import boto3
import boto3.exceptions
import github_api_toolkit
from botocore.exceptions import ClientError

# GitHub Organisation
org = os.getenv("GITHUB_ORG")

# GitHub App Client ID
client_id = os.getenv("GITHUB_APP_CLIENT_ID")

# AWS Secret Manager Secret Name for the .pem file
secret_name = os.getenv("AWS_SECRET_NAME")
secret_reigon = os.getenv("AWS_DEFAULT_REGION")

account = os.getenv("AWS_ACCOUNT_NAME")

# AWS Bucket Path
bucket_name = f"{account}-copilot-usage-dashboard"
object_name = "historic_usage_data.json"

logger = logging.getLogger()

# Example Log Output:
#
# Standard output:
# {
#     "timestamp":"2023-10-27T19:17:45.586Z",
#     "level":"INFO",
#     "message":"Inside the handler function",
#     "logger": "root",
#     "requestId":"79b4f56e-95b1-4643-9700-2807f4e68189"
# }
#
# Output with extra fields:
# {
#     "timestamp":"2023-10-27T19:17:45.586Z",
#     "level":"INFO",
#     "message":"Inside the handler function",
#     "logger": "root",
#     "requestId":"79b4f56e-95b1-4643-9700-2807f4e68189",
#     "records_added": 10
# }


def get_copilot_team_date(gh: github_api_toolkit.github_interface, page: int) -> list:
    """Gets a list of GitHub Teams with CoPilot Data for a given API page.

    Args:
        gh (github_api_toolkit.github_interface): An instance of the github_interface class.
        page (int): The page number of the API request.

    Returns:
        list: A list of GitHub Teams with CoPilot Data.
    """
    copilot_teams = []

    response = gh.get(f"/orgs/{org}/teams", params={"per_page": 100, "page": page})
    teams = response.json()
    for team in teams:
        usage_data = gh.get(f"/orgs/{org}/team/{team['name']}/copilot/metrics")
        try:
            if usage_data.json():
                copilot_teams.append(
                    {
                        "name": team.get("name", ""),
                        "slug": team.get("slug", ""),
                        "description": team.get("description", ""),
                        "url": team.get("html_url", ""),
                    }
                )
        except Exception as error:
            # If Exception, then the team does not have copilot usage data and can be skipped
            pass

    return copilot_teams

def handler(event, context):

    # Create an S3 client
    session = boto3.Session()
    s3 = session.client("s3")

    logger.info("S3 client created")

    # Get the .pem file from AWS Secrets Manager
    secret_manager = session.client("secretsmanager", region_name=secret_reigon)

    logger.info("Secret Manager client created")

    secret = secret_manager.get_secret_value(SecretId=secret_name)["SecretString"]

    # Get updated copilot usage data from GitHub API
    access_token = github_api_toolkit.get_token_as_installation(org, secret, client_id)

    if type(access_token) == str:
        logger.error(f"Error getting access token: {access_token}")
        return f"Error getting access token: {access_token}"
    else:
        logger.info(
            "Access token retrieved using AWS Secret",
            extra={"secret_address": secret_name},
        )

    # Create an instance of the api_controller class
    gh = github_api_toolkit.github_interface(access_token[0])

    logger.info("API Controller created")

    # CoPilot Usage Data (Historic)

    # Get the usage data
    usage_data = gh.get(f"/orgs/{org}/copilot/metrics")
    usage_data = usage_data.json()

    logger.info("Usage data retrieved")

    try:
        response = s3.get_object(Bucket=bucket_name, Key=object_name)
        historic_usage = json.loads(response["Body"].read().decode("utf-8"))
    except ClientError as e:
        logger.error(f"Error getting {object_name}: {e}")

        logger.info(f"Using empty list for {object_name}")
        historic_usage = []

    dates_added = []

    # Append the new usage data to the historic_usage_data.json
    for date in usage_data:
        if not any(d["date"] == date["date"] for d in historic_usage):
            historic_usage.append(date)

            dates_added.append(date["date"])

    logger.info(
        f"New usage data added to {object_name}",
        extra={"no_days_added": len(dates_added), "dates_added": dates_added},
    )

    # Write the updated historic_usage to historic_usage_data.json
    s3.put_object(
        Bucket=bucket_name,
        Key=object_name,
        Body=json.dumps(historic_usage, indent=4).encode("utf-8"),
    )

    logger.info(f"Uploaded updated {object_name} to S3")

    # GitHub Teams with CoPilot Data

    logger.info("Getting GitHub Teams with CoPilot Data")

    copilot_teams = []

    response = gh.get(f"/orgs/{org}/teams", params={"per_page": 100})

    # Get the last page of teams
    try:
        last_page = int(response.links["last"]["url"].split("=")[-1])
    except KeyError:
        last_page = 1

    for page in range(1, last_page + 1):
        page_teams = get_copilot_team_date(gh, page)

        copilot_teams = copilot_teams + page_teams

    logger.info(
        "Got GitHub Teams with CoPilot Data",
        extra={"no_teams": len(copilot_teams)},
    )

    s3.put_object(
        Bucket=bucket_name,
        Key="copilot_teams.json",
        Body=json.dumps(copilot_teams, indent=4).encode("utf-8"),
    )

    logger.info("Uploaded updated copilot_teams.json to S3")

    logger.info(
        "Process complete",
        extra={
            "bucket": bucket_name,
            "no_days_added": len(dates_added),
            "dates_added": dates_added,
            "no_dates_before": len(historic_usage) - len(dates_added),
            "no_dates_after": len(historic_usage),
            "no_copilot_teams": len(copilot_teams),
        },
    )

    # Get teams history
    team_history = []
    
    logger.info("Getting history of each team identified previously")

    # Retrieve existing team history from S3
    try:
        response = s3.get_object(Bucket=bucket_name, Key="teams_history.json")
        existing_team_history = json.loads(response["Body"].read().decode("utf-8"))
    except ClientError as e:
        logger.warning(f"Error retrieving existing team history: {e}")
        existing_team_history = []

    logger.info(f"Existing team history has {len(existing_team_history)} entries")

    # Create a dictionary for quick lookup of existing team data using the `name` field
    existing_team_data_map = {single_team["team"]["name"]: single_team for single_team in existing_team_history}

    # Iterate through identified teams
    for team in copilot_teams:
        team_name = team.get("name", "")
        if not team_name:
            logger.warning("Skipping team with no name")
            continue

        # Determine the last known date for the team
        last_known_date = None
        if team_name in existing_team_data_map:
            existing_dates = [entry["date"] for entry in existing_team_data_map[team_name]["data"]]
            if existing_dates:
                last_known_date = max(existing_dates)  # Get the most recent date

        # Assign the last know date to the `since` query parameter
        query_params = {}
        if last_known_date:
            query_params["since"] = last_known_date

        single_team_history = get_team_history(gh, org, team_name, query_params)
        if not single_team_history:
            logger.info(f"No new history found for team {team_name}")
            continue

        # Append new data to the existing team history
        new_team_data = single_team_history
        if team_name in existing_team_data_map:
            existing_team_data_map[team_name]["data"].extend(new_team_data)
        else:
            existing_team_data_map[team_name] = {"team": team, "data": new_team_data}

    # Convert the updated team data map back to a list
    updated_team_history = list(existing_team_data_map.values())

    # Write updated team history to S3
    s3.put_object(
        Bucket=bucket_name,
        Key="teams_history.json",
        Body=json.dumps(updated_team_history, indent=4).encode("utf-8"),
    )

    logger.info("Uploaded updated teams_history.json to S3")

    return "Github Data logging is now complete."


def get_team_history(gh: github_api_toolkit.github_interface, org: str, team: str, query_params: dict = None):
    """
    Gets the team metrics Copilot data through the API.
    Note - This endpoint will only return results for a given day if the team had
    five or more members with active Copilot licenses on that day,
    as evaluated at the end of that day.

    Args:
        gh (github_api_toolkit.github_interface): An instance of the github_interface class.
        org (str): Organisation name.
        team (str): Team name.
        query_params (dict): Additional query parameters for the API request.

    Returns:
        json: A json of team's GitHub team metrics or None if an error occurs.
    """
    try:
        response = gh.get(f"/orgs/{org}/team/{team}/copilot/metrics", params=query_params)
        return response.json()
    except Exception as e:
        logger.error(f"Error getting history for team {team} due to {e} with Github API")
        return None
    