import boto3
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
file_name = "/tmp/historic_usage_data.json"

logger = logging.getLogger()

def handler(event, context):
    file_exists = True

    logger.info("Starting process")

    logger.info("Creating S3 client")

    # Create an S3 client
    session = boto3.Session()
    s3 = session.client('s3')

    logger.info("S3 client created")

    logger.info("Getting historic_usage_data.json from S3")

    # Get historic_usage_data.json from S3
    try:
        s3.download_file(bucket_name, object_name, file_name)
    except ClientError as e:
        logger.exception("Error getting historic_usage_data.json from S3")
        file_exists = False
    else:
        logger.info("Downloaded historic_usage_data.json from S3")

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

    # If historic_usage_data.json exists, load it, else create an empty list
    if file_exists:
        with open(file_name, "r") as f:
            historic_usage = json.load(f)
            logger.info("Loaded historic_usage_data.json")
    else:
        logger.info("No historic_usage_data.json found, creating empty list")
        historic_usage = []

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

    # Write the updated historic_usage to historic_usage_data.json
    with open(file_name, "w") as f:
        f.write(json.dumps(historic_usage, indent=4))
        logger.info("Written changes to historic_usage_data.json")

    # Upload the updated historic_usage_data.json to S3
    s3.upload_file(file_name, bucket_name, object_name)

    logger.info("Uploaded updated historic_usage_data.json to S3")

    logger.info("Process complete")
    return("Process complete")