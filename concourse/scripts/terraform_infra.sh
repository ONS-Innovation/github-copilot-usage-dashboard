set -euo pipefail

aws_account_id=$(echo "$secrets" | jq -r .aws_account_id)
aws_access_key_id=$(echo "$secrets" | jq -r .aws_access_key_id)

aws_secret_access_key=$(echo "$secrets" | jq -r .aws_secret_access_key)
aws_secret_name=$(echo "$secrets" | jq -r .aws_secret_name)

env_name=$(echo "$secrets" | jq -r .env_name)
lambda_name=$(echo "$secrets" | jq -r .lambda_name)

github_app_client_id=$(echo "$secrets" | jq -r .github_app_client_id)
lambda_arch=$(echo "$secrets" | jq -r .lambda_arch)

github_org=$(echo "$secrets" | jq -r .github_org)
container_image=$(echo "$secrets" | jq -r .container_image)

schedule=$(echo "$secrets" | jq -r .schedule)
lambda_timeout=$(echo "$secrets" | jq -r .lambda_timeout)

export AWS_ACCESS_KEY_ID=$aws_access_key_id
export AWS_SECRET_ACCESS_KEY=$aws_secret_access_key

git config --global url."https://x-access-token:$github_access_token@github.com/".insteadOf "https://github.com/"

if [[ ${env} != "prod" ]]; then
	env="dev"
fi

cd resource-repo/terraform

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
	-var "lambda_timeout=$lambda_timeout" \
	-var "github_app_client_id=$github_app_client_id" \
	-var "github_org=$github_org" \
	-var "schedule=$schedule" \
	-auto-approve
