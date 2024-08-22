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

def handler(event, context):
    logger.info("Starting process")

    logger.info("Creating S3 client")

    # Create an S3 client
    session = boto3.Session()
    s3 = session.client('s3')

    logger.info("S3 client created")

    logger.info("Creating Secret Manager client")

    # Get the .pem file from AWS Secrets Manager
    secret_manager = session.client("secretsmanager", region_name=secret_reigon)

    logger.info("Secret Manager client created")

    logger.info("Getting secret from Secret Manager")

    secret = secret_manager.get_secret_value(SecretId=secret_name)["SecretString"]

    logger.info("Secret retrieved")

    logger.info("Getting access token")

    # Get updated copilot usage data from GitHub API
    access_token = github_api_toolkit.get_token_as_installation(org, secret, client_id)

    if type(access_token) == str:
        logger.error(f"Error getting access token: {access_token}")
        return(f"Error getting access token: {access_token}")
    else:
        logger.info("Access token retrieved")

    logger.info("Creating API Controller")

    # Create an instance of the api_controller class
    gh = github_api_toolkit.github_interface(access_token[0])

    logger.info("API Controller created")

    logger.info("Getting usage data from GitHub")

    # Get the usage data
    usage_data = gh.get(f"/orgs/{org}/copilot/usage")
    usage_data = usage_data.json()

    logger.info("Usage data retrieved")

    logger.info("Processing usage data")

    logger.info("Loading historic_usage_data.json")

    try:
        response = s3.get_object(Bucket=bucket_name, Key=object_name)
    except ClientError as e:
        logger.error(f"Error getting historic_usage_data.json: {e}")

        logger.info("Using empty list for historic_usage_data.json")
        historic_usage = []
    else:
        historic_usage = json.loads(response["Body"].read().decode("utf-8"))

    dates_added = []

    logger.info("Adding new usage data to historic_usage_data.json")

    # Append the new usage data to the historic_usage_data.json
    for day in usage_data:
        if not any(d["day"] == day["day"] for d in historic_usage):
            historic_usage.append(day)

            dates_added.append(day["day"])
    
    logger.info(
        "New usage data added to historic_usage_data.json",
        extra={
            "no_days_added": len(dates_added),
            "dates_added": dates_added
        }
    )

    s3.put_object(Bucket=bucket_name, Key=object_name, Body=json.dumps(historic_usage, indent=4).encode("utf-8"))

    logger.info("Uploaded updated historic_usage_data.json to S3")

    logger.info("Process complete")
    return("Process complete")