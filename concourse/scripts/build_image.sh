#!/usr/bin/env bash

# shellcheck disable=SC3040,SC2154,SC2148
set -euo pipefail

export STORAGE_DRIVER=vfs
export PODMAN_SYSTEMD_UNIT=concourse-task

# shellcheck disable=SC2154
container_image=$(echo "$secrets" | jq -r .container_image)

# shellcheck disable=SC2154
aws ecr get-login-password --region eu-west-2 | podman --storage-driver=vfs login --username AWS --password-stdin ${aws_account_id}.dkr.ecr.eu-west-2.amazonaws.com

# shellcheck disable=SC2154
podman build -t ${container_image}:${tag} resource-repo/src/

# shellcheck disable=SC2154
podman tag ${container_image}:${tag} ${aws_account_id}.dkr.ecr.eu-west-2.amazonaws.com/${container_image}:${tag}

# shellcheck disable=SC2154
podman push ${aws_account_id}.dkr.ecr.eu-west-2.amazonaws.com/${container_image}:${tag}
