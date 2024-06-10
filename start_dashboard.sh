#! /bin/sh

# Retrieve the Github App secret from AWS Secret Manager
# and store the value in a file.
# If running the script on local dev use: --profile <aws_credential_profile> to 
# specify the credentials to use.
aws secretsmanager get-secret-value --secret-id "/sdp/tools/copilot-usage/copilot-usage-dashboard.pem" --region eu-west-2 --query SecretString --output text > ./copilot-usage-dashboard.pem

# Activate the virtual environment created by poetry install in the dockerfile
. ./.venv/bin/activate

# Start the application
streamlit run src/app.py --server.port=8501 --server.address=0.0.0.0