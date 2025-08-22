#!/usr/bin/env bash

# shellcheck disable=SC3040,SC2154,SC2148
set -euo pipefail

AWS_ACCESS_KEY_ID="$(cat AccessKeyId)"
AWS_SECRET_ACCESS_KEY="$(cat SecretAccessKey)"
AWS_SESSION_TOKEN="$(cat SessionToken)"

# shellcheck disable=SC3040,SC2154
aws sts assume-role --output text \
	--role-arn "${aws_role_arn}" \
	--role-session-name concourse-pipeline-run \
	--query "Credentials.[AccessKeyId,SecretAccessKey,SessionToken]" |
	awk -F '\t' '{print $1 > ("AccessKeyId")}{print $2 > ("SecretAccessKey")}{print $3 > ("SessionToken")}'

# shellcheck disable=SC3040,SC2154
export AWS_ACCESS_KEY_ID
export AWS_SECRET_ACCESS_KEY
export AWS_SESSION_TOKEN
