# aws ecr get-login-password --region eu-west-2 | docker login --username AWS --password-stdin 381492126214.dkr.ecr.eu-west-2.amazonaws.com

# docker build -t sdp-dev-copilot-usage .

# docker tag sdp-dev-copilot-usage:latest 381492126214.dkr.ecr.eu-west-2.amazonaws.com/sdp-dev-copilot-usage:latest

# docker push 381492126214.dkr.ecr.eu-west-2.amazonaws.com/sdp-dev-copilot-usage:latest

#!/bin/bash

# Function to validate the semantic versioning format
# Example formats that are allowed are:
# v1.0.0
# v1.0.0-alpha
# v1.0.0-rc1
validate_semver() {
    local version=$1

    # Regular expression for semantic versioning (supports optional pre-release)
    semver_regex="^v([0-9]+)\.([0-9]+)\.([0-9]+)(-[0-9A-Za-z-]+)?$"

    if [[ $version =~ $semver_regex ]]; then
        echo "Valid semantic version: $version"
        return 0
    else
        echo "Invalid version format: $version"
        return 1
    fi
}

# Check if a profile name is passed as an argument
if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ] || [ -z "$4" ] ; then
  echo "Usage: $0 <aws profile e.g ons_sdp_sandbox> <AWS account ID e.g 123456789> <env e.g sdp-sandbox> <container-ver e.g 1.0.0>"
  exit 1
fi

PROFILE=$1
ACCOUNT=$2
ENV=$3
VER=$4
IMAGE_NAME=copilot-usage

# Check if the environment matches expected values
if [ "$3" != "sdp-sandbox" ] && [ "$3" != "sdp-dev" ] && [ "$3" != "sdp-prod" ]; then
  echo "Usage: $0 env must be one of sdp-sandbox or sdp-dev or sdp-prod"
  exit 1
else
    ENV=$3
fi

# Check if the version number is passed as an argument
if [ "$4" ]; then
  # Check it meets semver format
  validate_semver $VER
  if [ $? -ne 0 ]; then
    echo "Usage: $0 container-ver must be a valid version number e.g v1.0.0 or v1.0.0-alpha or v1.0.0-rc1"
    exit 1
  else
    # Check if the version already exists in the repository
    IMAGE_EXISTS=$(aws ecr describe-images --profile $PROFILE --region "eu-west-2" --repository-name "$ENV-$IMAGE_NAME" --query "imageDetails[?contains(imageTags, '$VER')]" --output text)
    if [ -n "$IMAGE_EXISTS" ]; then
      echo "Docker image with tag $VER already exists in repository $ENV-$IMAGE_NAME. Rename, remove or use a different version number"
      exit 1
    else:
      # Reset the IMAGE_EXISTS variable
      IMAGE_EXISTS=""
    fi
  fi
fi

aws ecr get-login-password --profile $PROFILE --region eu-west-2 | docker login --username AWS --password-stdin $ACCOUNT.dkr.ecr.eu-west-2.amazonaws.com

echo "Building Docker image: $IMAGE_NAME with tag: $VER"
docker build -t $IMAGE_NAME:$VER .

# Check if the Docker build command was successful
if [ $? -ne 0 ]; then
  echo "Docker build failed"
  exit 1
fi

# Wait for the build to finish
echo "Docker build completed. Verifying the image exists..."

# Run docker images to check if the image exists
if docker images | grep -q "$IMAGE_NAME.*$VER"; then
  echo "Docker image $IMAGE_NAME:$VER exists"
else
  echo "Docker image $IMAGE_NAME:$VER not found"
  exit 1
fi

echo "Tagging Docker image: $IMAGE_NAME with tag: $VER"
docker tag $IMAGE_NAME:$VER $ACCOUNT.dkr.ecr.eu-west-2.amazonaws.com/$ENV-$IMAGE_NAME:$VER

echo "Pushing Docker image: $IMAGE_NAME with tag: $VER to ECR"
docker push $ACCOUNT.dkr.ecr.eu-west-2.amazonaws.com/$ENV-$IMAGE_NAME:$VER

if [ $? -ne 0 ]; then
  echo "Docker push failed"
  exit 1
fi

IMAGE_EXISTS=$(aws ecr describe-images --profile $PROFILE --region "eu-west-2" --repository-name "$ENV-$IMAGE_NAME" --query "imageDetails[?contains(imageTags, '$VER')]" --output text)

if [ -n "$IMAGE_EXISTS" ]; then
  echo "Success - Docker image with tag $VER exists in repository $ENV-$IMAGE_NAME"
else
  echo "Failure - Docker image with tag $VER does not exist in repository $ENV-$IMAGE_NAME"
  exit 1
fi