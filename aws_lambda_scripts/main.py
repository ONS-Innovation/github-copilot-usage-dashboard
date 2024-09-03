import boto3
import boto3.exceptions
from botocore.exceptions import ClientError
import json
import os
import logging

import github_api_toolkit

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

def handler(event, context):

    # Create an S3 client
    session = boto3.Session()
    s3 = session.client('s3')

    logger.info("S3 client created")

    # Get the .pem file from AWS Secrets Manager
    secret_manager = session.client("secretsmanager", region_name=secret_reigon)

    logger.info("Secret Manager client created")

    secret = secret_manager.get_secret_value(SecretId=secret_name)["SecretString"]

    # Get updated copilot usage data from GitHub API
    access_token = github_api_toolkit.get_token_as_installation(org, secret, client_id)

    if type(access_token) == str:
        logger.error(f"Error getting access token: {access_token}")
        return(f"Error getting access token: {access_token}")
    else:
        logger.info(
            "Access token retrieved using AWS Secret",
            extra = {
                "secret_address": secret_name
            }
        )

    # Create an instance of the api_controller class
    gh = github_api_toolkit.github_interface(access_token[0])

    logger.info("API Controller created")

    # Get the usage data
    usage_data = gh.get(f"/orgs/{org}/copilot/usage")
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
    for day in usage_data:
        if not any(d["day"] == day["day"] for d in historic_usage):
            historic_usage.append(day)

            dates_added.append(day["day"])
    
    logger.info(
        f"New usage data added to {object_name}",
        extra={
            "no_days_added": len(dates_added),
            "dates_added": dates_added
        }
    )

    # Write the updated historic_usage to historic_usage_data.json
    s3.put_object(Bucket=bucket_name, Key=object_name, Body=json.dumps(historic_usage, indent=4).encode("utf-8"))

    logger.info(f"Uploaded updated {object_name} to S3")

    logger.info(
        "Process complete",
        extra = {
            "bucket": bucket_name,
            "no_days_added": len(dates_added),
            "dates_added": dates_added,
            "no_dates_before": len(historic_usage) - len(dates_added),
            "no_dates_after": len(historic_usage)
        }
    )