set -euo pipefail

apk add --no-cache jq

aws_account_id=$(echo "$github_copilot_secrets" | jq -r .aws_account_id)
aws_access_key_id=$(echo "$github_copilot_secrets" | jq -r .aws_access_key_id)

aws_secret_access_key=$(echo "$github_copilot_secrets" | jq -r .aws_secret_access_key)
aws_secret_name=$(echo "$github_copilot_secrets" | jq -r .aws_secret_name)

env_name=$(echo "$github_copilot_secrets" | jq -r .env_name)
lambda_name=$(echo "$github_copilot_secrets" | jq -r .lambda_name)

github_app_client_id=$(echo "$github_copilot_secrets" | jq -r .github_app_client_id)
lambda_arch=$(echo "$github_copilot_secrets" | jq -r .lambda_arch)

github_org=$(echo "$github_copilot_secrets" | jq -r .github_org)
container_image=$(echo "$github_copilot_secrets" | jq -r .container_image)

schedule=$(echo "$github_copilot_secrets" | jq -r .schedule)
lambda_timeout=$(echo "$github_copilot_secrets" | jq -r .lambda_timeout)

export AWS_ACCESS_KEY_ID=$aws_access_key_id
export AWS_SECRET_ACCESS_KEY=$aws_secret_access_key

git config --global url."https://x-access-token:$github_access_token@github.com/".insteadOf "https://github.com/"

if [[ ${env} != "prod" ]]; then
    env="dev"
fi

cd resource-repo/terraform/data_logger/

terraform init -backend-config=env/${env}/backend-${env}.tfbackend -reconfigure

terraform apply \
-var "aws_account_id=$aws_account_id" \
-var "aws_access_key_id=$aws_access_key_id" \
-var "aws_secret_access_key=$aws_secret_access_key" \
-var "aws_secret_name=$aws_secret_name" \
-var "env_name=$env_name" \
-var "lambda_version=${tag}" \
-var "lambda_name=$lambda_name" \
-var "lambda_arch=$lambda_arch" \
-var "github_app_client_id=$github_app_client_id" \
-var "github_org=$github_org" \
-var "schedule=$schedule" \
-auto-approve