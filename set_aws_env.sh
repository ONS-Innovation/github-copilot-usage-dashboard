#! /bin/sh

# The script expects the aws credentials file to be located at ~/.aws/credentials
# The credentials file should have the following format, [proflie-name]:
# personal aws account
# [default]
# aws_access_key_id = EXAMPLEACCESSKEY
# aws_secret_access_key = EXAMPLESECRETACCESSKEY
# [ecr_account]
# aws_access_key_id = EXAMPLEACCESSKEY-ECR
# aws_secret_access_key = EXAMPLESECRETACCESSKEY-ECR
# # organisation aws account
# [ons_sdp_sandbox]
# aws_access_key_id = EXAMPLEACCESSKEY-SANDBOX
# aws_secret_access_key = EXAMPLESECRETACCESSKEY-SANDBOX


#!/bin/bash

# Check if a profile name is passed as an argument
if [ -z "$1" ] || [ -z "$2" ]; then
  echo "Usage: $0 <profile-name e.g ons_sdp_sandbox> <env e.g sdp-sandbox>"
  exit 1
fi

PROFILE=$1
CREDENTIALS_FILE="$HOME/.aws/credentials"

# Check if the environment matches expected values
if [ "$2" != "sdp-sandbox" ] && [ "$2" != "sdp-dev" ]; then
  echo "Usage: $0 env must be one of sdp-sandbox or sdp-dev"
  exit 1
else
    ENV=$2
fi

# Check if the credentials file exists
if [ ! -f "$CREDENTIALS_FILE" ]; then
  echo "Credentials file not found: $CREDENTIALS_FILE"
  echo "Set one up by installing aws cli and running: aws configure"
  exit 1
fi

# Read the credentials file and set environment variables based on the profile
while IFS= read -r line; do
  # Skip empty lines and comments
  if [[ -z "$line" || "$line" =~ ^# ]]; then
    continue
  fi

  # Check if the line is a profile header
  if [[ "$line" =~ ^\[(.*)\]$ ]]; then
    CURRENT_PROFILE="${BASH_REMATCH[1]}"
  fi

  # If the current profile matches the specified profile, set the variables
  if [[ "$CURRENT_PROFILE" == "$PROFILE" ]]; then
    if [[ "$line" =~ aws_access_key_id[[:space:]]*=[[:space:]]*(.*) ]]; then
      export AWS_ACCESS_KEY_ID="${BASH_REMATCH[1]}"
    elif [[ "$line" =~ aws_secret_access_key[[:space:]]*=[[:space:]]*(.*) ]]; then
      export AWS_SECRET_ACCESS_KEY="${BASH_REMATCH[1]}"
    fi
  fi
done < "$CREDENTIALS_FILE"

# Check if the environment variables were set
if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
  echo "Failed to set environment variables for profile: $PROFILE"
  exit 1
fi

export AWS_DEFAULT_REGION="eu-west-2"
export APP_NAME=$ENV"-copilot-usage"

echo "Environment variables are set as:"
echo "export AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID"
echo "export AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY"
echo "export AWS_DEFAULT_REGION=eu-west-2"
echo "export APP_NAME=$APP_NAME"