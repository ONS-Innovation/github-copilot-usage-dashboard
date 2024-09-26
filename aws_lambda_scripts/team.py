import boto3
import boto3.exceptions
from botocore.exceptions import ClientError
import json
import os
import logging

import github_api_toolkit
from datetime import datetime, timedelta

# GitHub Organisation
org = os.getenv("GITHUB_ORG")
secret_reigon = os.getenv("AWS_DEFAULT_REGION")
secret_name = os.getenv("AWS_SECRET_NAME")

# GitHub App Client ID
client_id = os.getenv("GITHUB_APP_CLIENT_ID")
session = boto3.Session()
s3 = session.client("s3")


# Get the .pem file from AWS Secrets Manager
secret_manager = session.client("secretsmanager", region_name=secret_reigon)


secret = secret_manager.get_secret_value(SecretId=secret_name)["SecretString"]

# Get updated copilot usage data from GitHub API
access_token = github_api_toolkit.get_token_as_installation(org, secret, client_id)
print(access_token)

# Create an instance of the api_controller class
gh = github_api_toolkit.github_interface(access_token[0])


# Get the usage data with query parameters
usage_data = gh.get(
    f"/orgs/{org}/team/keh-dev/copilot/usage",
)
usage_data = usage_data.json()
print(org, usage_data)
# Define the path to the output JSON file
output_path = os.path.join(os.path.dirname(__file__), "../src/data.json")

# Ensure the directory exists
os.makedirs(os.path.dirname(output_path), exist_ok=True)

# Write the usage data to the JSON file
with open(output_path, "w") as json_file:
    json.dump(usage_data, json_file, indent=4)

print(f"Usage data has been written to {output_path}")
