import streamlit as st
import os
import boto3
import github_api_toolkit
from typing import Any, Tuple
from datetime import datetime
import pandas as pd

org = os.getenv("GITHUB_ORG")                           # The name of the organisation to query
app_client_id = os.getenv("GITHUB_APP_CLIENT_ID")       # The client id for the GitHub App used to make requests
aws_default_region = os.getenv("AWS_DEFAULT_REGION")    # The AWS region the secret is in 
aws_secret_name = os.getenv("AWS_SECRET_NAME")          # Path to the .pem file in Secret Manager on AWS

def get_access_token(secret_manager: Any, secret_name: str, org: str, app_client_id: str) -> Tuple[str, str]:
    """Gets the access token from the AWS Secret Manager.
    Args:
        secret_manager (Any): The Boto3 Secret Manager client.
        secret_name (str): The name of the secret to get.
        org (str): The name of the GitHub organization.
        app_client_id (str): The client ID of the GitHub App.
    Raises:
        Exception: If the secret is not found in the Secret Manager.
    Returns:
        str: The access token.
    """
    response = secret_manager.get_secret_value(SecretId=secret_name)
    pem_contents = response.get("SecretString", "")
    if not pem_contents:
        error_message = (
            f"Secret {secret_name} not found in AWS Secret Manager. Please check your environment variables."
        )
        raise Exception(error_message)
    token = github_api_toolkit.get_token_as_installation(org, pem_contents, app_client_id)
    if type(token) is not tuple:
        raise Exception(token)
    return token

session = boto3.session.Session() # Create a Boto3 session
 
secret_manager = session.client(service_name="secretsmanager", region_name=aws_default_region) # Create a Secret Manager Client

token = get_access_token(secret_manager, aws_secret_name, org, app_client_id) # Get Auth Token
 
rest = github_api_toolkit.github_interface(token[0]) # Setup github_interface()

response = rest.get('/orgs/ONSDigital/copilot/metrics')

usage_data = response.json()

min_date = datetime.strptime(usage_data[0]["date"], "%Y-%m-%d")
max_date = datetime.strptime(usage_data[-1]["date"], "%Y-%m-%d")

# Create a date slider with the full range selected by default
if min_date == max_date:
    min_date -= pd.Timedelta(days=1)

date_range = st.slider(
    "Date range",
    min_value=min_date,
    max_value=max_date,
    value=(min_date, max_date),
    format="YYYY-MM-DD",
)

st.json(usage_data)

@st.cache_data
def generate_datasets(date_range: tuple):
    
    df_usage_data = pd.json_normalize(usage_data) # Converts copilot_usage_data.json into a dataframe
    df_usage_data["date"] = df_usage_data["date"].apply(lambda x: datetime.strptime(x, "%Y-%m-%d")) # Convert date column from str to datetime
    df_usage_data["display_date"] = df_usage_data["date"].apply(lambda x: datetime.strftime(x, "%d %b")) # Create a short version of the day

    # Create a subset of data based on slider selection
    df_usage_data_subset = df_usage_data.loc[
        (df_usage_data["date"] >= date_range[0]) & (df_usage_data["date"] <= date_range[1])
    ].reset_index(drop=True)

    copilot_chat = pd.DataFrame()
    ide_completions = pd.DataFrame()

    for i in range (len(df_usage_data_subset.date)):
        print(df_usage_data_subset.date[i])
        
        # Get copilot chat data

        # for model in df_usage_data_subset[i]["copilot_ide_chat_editors_models"]:
        #     chat_data = pd.DataFrame([{
        #         "total_chats": model.get("total_chats", 0),
        #         "total_engaged_users": model.get("total_engaged_users", 0),
        #         "total_copies": model.get("total_chat_copy_events", 0),
        #         "total_insertions": model.get("total_chat_insertion_events", 0),
        #     }])
        #     copilot_chat = pd.concat([copilot_chat, chat_data], ignore_index=True)

        #TODO: Get IDE completions data

    return (
        df_usage_data_subset,
        copilot_chat,
        ide_completions
    )

(
    df_usage_data_subset,
    copilot_chat,
    ide_completions,
) = generate_datasets(date_range)

#TODO: Calculate totals


st.logo("./src/branding/ONS_Logo_Digital_Colour_Landscape_Bilingual_RGB.svg")

col1, col2 = st.columns([0.8, 0.2])
col1.title(":blue-background[Interim Page]")
col2.image("./src/branding/ONS_Logo_Digital_Colour_Landscape_Bilingual_RGB.png")
st.write("This page serves as a temporary fix for an update in GitHub's APIs by using the new API endpoints.")

# IDE Code Completions Metrics
st.header(":blue-background[IDE Code Completions]")

# Display Metrics
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Acceptances", 0, border=True)
col2.metric("Total Suggestions", 0, border=True)
col3.metric("Total Lines of Code Suggested", 0, border=True)
col4.metric("Total Lines of Code Accepted", 0, border=True)

st.metric("Acceptance Rate", 0, border=True)

# CoPilot Chat Metrics
st.header(":blue-background[CoPilot Chat]")

# Display Metrics
col1, col2, col3 = st.columns(3)
col1.metric("Total Sessions", 0, border=True)
col2.metric("Total Insertions", 0, border=True)
col3.metric("Total Copies", 0, border=True)

col1, col2 = st.columns(2)
col1.metric("Insert Rate", 0, border=True)
col2.metric("Copy Rate", 0, border=True)

st.header(":blue-background[Seat Information]")
# TODO: Add seat information here