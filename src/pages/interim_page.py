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

# Get usage data
response = rest.get(f"/orgs/{org}/copilot/metrics")
usage_data = response.json()

# Get seat data
response = rest.get(f"/orgs/{org}/copilot/billing/seats", params={"per_page": 100})
seat_data = response.json()

try:
    last_page = int(response.links["last"]["url"].split("=")[-1])
except KeyError:
    # If Key Error, Last doesn't exist therefore 1 page
    last_page = 1
    
# Skip first page as we already have it
for i in range(1, last_page):
    response = rest.get(f"/orgs/{org}/copilot/billing/seats", params={"per_page": 100, "page": i + 1})

    seat_data["seats"].append(response.json()["seats"])

df_seat_data = pd.DataFrame()

# Puts the seat information from copilot_seats_data.json into a dataframe
for row in seat_data["seats"]:
    df_seat_data = pd.concat([df_seat_data, pd.json_normalize(row)], ignore_index=True)

# Converts last_activity_at to a formatted string
df_seat_data["last_activity_at"] = df_seat_data["last_activity_at"].apply(
    lambda x: datetime.strptime(str(x), "%Y-%m-%dT%H:%M:%SZ") if pd.notna(x) and x not in (None, "") else None
)

min_date = datetime.strptime(usage_data[0]["date"], "%Y-%m-%d")
max_date = datetime.strptime(usage_data[-1]["date"], "%Y-%m-%d")

# Create a date slider with the full range selected by default
if min_date == max_date:
    min_date -= pd.Timedelta(days=1)

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

        # Get copilot chat data
        editors_data = df_usage_data_subset.iloc[i]["copilot_ide_chat.editors"]

        for editor in editors_data:
            editor_name = editor.get("name", "")
            models_data = editor.get("models", [])

            for model in models_data:
                data = pd.DataFrame([{
                    "editor_name": editor_name,
                    "model_name": model.get("name", ""),
                    "total_chats": model.get("total_chats", 0),
                    "total_engaged_users": model.get("total_engaged_users", 0),
                    "total_copies": model.get("total_chat_copy_events", 0),
                    "total_insertions": model.get("total_chat_insertion_events", 0),
                }])
                copilot_chat = pd.concat([copilot_chat, data], ignore_index=True)


        # Get IDE completions data
        editors_data = df_usage_data_subset.iloc[i]["copilot_ide_code_completions.editors"]

        for editor in editors_data:
            editor_name = editor.get("name", "")
            models_data = editor.get("models", [])

            for model in models_data:
                languages_data = model.get("languages", [])
                for language in languages_data:
                    data = pd.DataFrame([{
                        "editor_name": editor_name,
                        "model_name": model.get("name", ""),
                        "language_name": language.get("name", ""),
                        "engaged_users": language.get("total_engaged_users", 0),
                        "code_acceptances": language.get("total_code_acceptances", 0),
                        "code_suggestions": language.get("total_code_suggestions", 0),
                        "lines_of_code_suggested": language.get("total_code_lines_suggested", 0),
                        "lines_of_code_accepted": language.get("total_code_lines_accepted", 0),
                    }])
                    ide_completions = pd.concat([ide_completions, data], ignore_index=True)

    return (
        df_usage_data_subset,
        copilot_chat,
        ide_completions
    )

st.logo("./src/branding/ONS_Logo_Digital_Colour_Landscape_Bilingual_RGB.svg")

col1, col2 = st.columns([0.8, 0.2])
col1.title(":blue-background[Interim Page]")
col2.image("./src/branding/ONS_Logo_Digital_Colour_Landscape_Bilingual_RGB.png")
st.write("This page serves as a fix for an update in GitHub's APIs by using the new API endpoints.")

date_range = st.slider(
    "Date range",
    min_value=min_date,
    max_value=max_date,
    value=(min_date, max_date),
    format="YYYY-MM-DD",
)

(
    df_usage_data_subset,
    copilot_chat,
    ide_completions,
) = generate_datasets(date_range)

# Calculate totals
copilot_chat_totals = copilot_chat[["total_chats", "total_engaged_users", "total_copies", "total_insertions"]].sum()
ide_completions_totals = ide_completions[["engaged_users", "code_acceptances", "code_suggestions", "lines_of_code_suggested", "lines_of_code_accepted"]].sum()

# IDE Code Completions Metrics
st.header(":blue-background[IDE Code Completions]")

# Display Metrics
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric(
    "Total Acceptances",
    ide_completions_totals['code_acceptances'],
    border=True
    )
col2.metric(
    "Total Suggestions",
    ide_completions_totals['code_suggestions'],
    border=True
    )
col3.metric(
    "Total Lines of Code Accepted",
    ide_completions_totals['lines_of_code_accepted'],
    border=True
    )
col4.metric(
    "Total Lines of Code Suggested",
    ide_completions_totals['lines_of_code_suggested'],
    border=True
    )
col5.metric(
    "Acceptance Rate",
    f"{round(ide_completions_totals['code_acceptances'] / ide_completions_totals['code_suggestions'] * 100, 2)}%",
    border=True
    )

# CoPilot Chat Metrics
st.header(":blue-background[CoPilot Chat]")

# Display Metrics
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric(
    "Total Chats",
    copilot_chat_totals['total_chats'],
    border=True
    )
col2.metric(
    "Total Insertions",
    copilot_chat_totals['total_insertions'],
    border=True
    )
col3.metric(
    "Total Copies",
    copilot_chat_totals['total_copies'],
    border=True
    )
col4.metric(
    "Insert Rate",
    f"{round(copilot_chat_totals['total_insertions'] / copilot_chat_totals['total_chats'] * 100, 2)}%",
    border=True
    )
col5.metric(
    "Copy Rate",
    f"{round(copilot_chat_totals['total_copies'] / copilot_chat_totals['total_chats'] * 100, 2)}%",
    border=True
    )

# Seat information
st.header(":blue-background[Seat Information]")

st.subheader("Inactivity Threshold")

inactivity_threshold = st.number_input("Inactive after x days:", value=28, step=1)

inactivity_date = datetime.now() - pd.Timedelta(days=inactivity_threshold)

st.write("Users are considered inactive after:", inactivity_date.strftime("%-d %B %Y"))

st.divider()

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Number of Seats", seat_data["total_seats"], border=True)

with col2:
    number_of_engaged_users = 0

    for index, row in df_seat_data.iterrows():
        if row.last_activity_at >= inactivity_date:
            number_of_engaged_users += 1

    st.metric("Number of Engaged Users", number_of_engaged_users, border=True)

with col3:
    number_of_inactive_users = seat_data["total_seats"] - number_of_engaged_users

    st.metric("Number of Inactive Users", number_of_inactive_users, border=True)

col1, col2 = st.columns(2)

with col1:
    st.subheader("Active Users")

    # Dataframe showing only active users (this with a latest activity)
    st.dataframe(
        df_seat_data.loc[df_seat_data["last_activity_at"] >= inactivity_date][
            ["assignee.login", "last_activity_at", "assignee.html_url"]
        ],
        hide_index=True,
        use_container_width=True,
        column_config={
            "assignee.login": st.column_config.Column("User"),
            "last_activity_at": st.column_config.DatetimeColumn("Last Activity At", format="YYYY-MM-DD HH:mm"),
            "assignee.html_url": st.column_config.LinkColumn(
                "Github Profile",
                help="A link to this user's profile",
                display_text="Go to Profile",
            ),
        },
    )

with col2:
    st.subheader("Inactive Users")

    # Dataframe showing only inactive users (those where last_activity_at is None)
    st.dataframe(
        df_seat_data.loc[(df_seat_data["last_activity_at"].isnull()) | (df_seat_data["last_activity_at"] < inactivity_date)][
            ["assignee.login", "last_activity_at", "assignee.html_url"]
        ],
        hide_index=True,
        use_container_width=True,
        column_config={
            "assignee.login": st.column_config.Column("User"),
            "last_activity_at": st.column_config.DatetimeColumn("Last Activity At", format="YYYY-MM-DD HH:mm"),
            "assignee.html_url": st.column_config.LinkColumn(
                "Github Profile",
                help="A link to this user's profile",
                display_text="Go to Profile",
            ),
        },
    )