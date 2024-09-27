import os
from datetime import datetime
from urllib.parse import urlencode

import boto3
import github_api_toolkit
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
from plotly.subplots import make_subplots

org = os.getenv("GITHUB_ORG")

# GitHub App Client ID
org_client_id = os.getenv("GITHUB_APP_CLIENT_ID")

# AWS Secret Manager Secret Name for the .pem file
secret_name = os.getenv("AWS_SECRET_NAME")
secret_reigon = os.getenv("AWS_DEFAULT_REGION")

account = os.getenv("AWS_ACCOUNT_NAME")

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
authorize_url = "https://github.com/login/oauth/authorize"
access_token_url = "https://github.com/login/oauth/access_token"
user_api_url = "https://api.github.com/user"
redirect_uri = "http://localhost:8502/team_usage"

session = boto3.Session()
s3 = session.client("s3")
secret_manager = session.client("secretsmanager", region_name=secret_reigon)


secret = secret_manager.get_secret_value(SecretId=secret_name)["SecretString"]

# Get updated copilot usage data from GitHub API
access_token = github_api_toolkit.get_token_as_installation(org, secret, org_client_id)
gh = github_api_toolkit.github_interface(access_token[0])

@st.cache_data(show_spinner=True)
def get_access_token(code):
    """Exchange code for access token"""
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "redirect_uri": redirect_uri,
        "scope": "user:email",
    }
    headers = {"Accept": "application/json"}
    response = requests.post(access_token_url, data=data, headers=headers)
    response.raise_for_status()
    access_token = response.json().get("access_token")
    st.session_state.access_token = access_token
    return access_token


def get_user_profile(access_token):
    """Fetch authenticated user's GitHub profile"""
    headers = {"Authorization": f"token {access_token}"}
    response = requests.get(user_api_url, headers=headers)
    response.raise_for_status()
    return response.json()


def is_user_in_org(username, org):
    orgs = gh.get(f"/orgs/{org}/members/{username}")
    if orgs.status_code == 204:
        return get_org_access_token()
    else: return False

def get_org_access_token():
    secret = get_pem_from_secret_manager(session, secret_name, secret_reigon)
    access_token = github_api_toolkit.get_token_as_installation(org, secret, org_client_id)

    return access_token

@st.cache_data
def get_pem_from_secret_manager(_session: boto3.Session, secret_name: str, region_name: str) -> str:
    """Gets the .pem file contents from AWS Secret Manager"""
    secret_manager = session.client("secretsmanager", region_name=region_name)
    return secret_manager.get_secret_value(SecretId=secret_name)["SecretString"]


def generate_datasets(date_range: tuple, usage_data):
    """Converts the JSON responses from the Github API into Pandas Dataframes"""
    # Convert copilot_usage_data.json into a dataframe
    df_usage_data = pd.json_normalize(usage_data)

    # Convert date column from str to datetime
    df_usage_data["day"] = df_usage_data["day"].apply(lambda x: datetime.strptime(x, "%Y-%m-%d"))

    # Create a short version of the day
    df_usage_data["display_day"] = df_usage_data["day"].apply(lambda x: datetime.strftime(x, "%d %b"))

    # Add a column for number of ignored results
    df_usage_data["total_decline_count"] = df_usage_data.total_suggestions_count - df_usage_data.total_acceptances_count

    # Add an acceptance rate column
    df_usage_data["acceptance_rate"] = round(
        df_usage_data.total_acceptances_count / df_usage_data.total_suggestions_count * 100, 2
    )

    # Create a subset of data based on slider selection
    df_usage_data_subset = df_usage_data.loc[
        (df_usage_data["day"] >= date_range[0]) & (df_usage_data["day"] <= date_range[1])
    ].reset_index(drop=True)

    # Breakdown Data
    breakdown = pd.DataFrame()
    for i in range(0, len(df_usage_data_subset.day)):
        for d in df_usage_data_subset.breakdown[i]:
            d["day"] = df_usage_data_subset.day[i]
        breakdown = pd.concat([breakdown, pd.json_normalize(df_usage_data_subset.breakdown[i])], ignore_index=True)

    # Group breakdown data by language
    breakdown_subset = breakdown.drop(columns=["editor", "active_users", "day"])
    language_grouped_breakdown = breakdown_subset.groupby(["language"]).sum()
    language_grouped_breakdown["acceptance_rate"] = round(
        (language_grouped_breakdown["acceptances_count"] / language_grouped_breakdown["suggestions_count"]), 2
    )

    # Group breakdown data by editor (IDE)
    breakdown_subset = breakdown.drop(columns=["language"])
    editor_grouped_breakdown_avg = breakdown_subset.groupby(["editor", "day"]).mean().reset_index()
    editor_grouped_breakdown_sum = breakdown_subset.groupby(["editor", "day"]).sum().reset_index()

    return (
        df_usage_data_subset,
        breakdown,
        language_grouped_breakdown,
        editor_grouped_breakdown_avg,
        editor_grouped_breakdown_sum,
    )


# Streamlit UI starts here
st.logo("./src/branding/ONS_Logo_Digital_Colour_Landscape_Bilingual_RGB.svg")
col1, col2 = st.columns([0.8, 0.2])

col1.title(":blue-background[GitHub Team Copilot Usage]")

col2.image("./src/branding/ONS_Logo_Digital_Colour_Landscape_Bilingual_RGB.png")

if "profile" not in st.session_state:
    st.session_state.profile = None
if "slugs" not in st.session_state:
    st.session_state.slugs = []

# Step 1: GitHub Login
if st.session_state.profile is None:
    login_url = (
        f"{authorize_url}?{urlencode({'client_id': client_id, 'redirect_uri': redirect_uri, 'scope': 'user:email'})}"
    )
    st.link_button("Login with GitHub", login_url)
    query_params = st.query_params
    if "code" in query_params:
        code = query_params["code"]
        try:
            access_token = get_access_token(code)
            profile = get_user_profile(access_token)
            st.session_state.profile = profile
            st.query_params.clear()
        except Exception as e:
            st.error(f"Error during login: {e}")
if st.session_state.profile is not None:
    profile = st.session_state.profile
    st.success(f"Hello, {profile['login']}!")
    access_token = is_user_in_org(profile["login"], org)

    if access_token:
        team_slug = st.text_input("Enter team name:")
        if team_slug and isinstance(access_token, tuple):
            if team_slug not in st.session_state:
                gh = github_api_toolkit.github_interface(access_token[0])

                usage_data = gh.get(f"/orgs/{org}/team/{team_slug}/copilot/usage")
                try:
                    usage_data = usage_data.json()
                    if usage_data:
                        st.session_state[team_slug] = usage_data
                    else:
                        st.error(f"The user '{profile["login"]}', from the '{org}' organization, is not in the '{team_slug}' team.")
                        st.stop()
                except Exception as error:
                    print(error)
                    st.error("Team does not exist.")
                    st.stop()
                    
            else:
                usage_data = st.session_state[team_slug]

            st.markdown(f"### {team_slug} Team Copilot Usage")


            # Get the maximum and minimum date which we have data for
            min_date = datetime.strptime(usage_data[0]["day"], "%Y-%m-%d")
            max_date = datetime.strptime(usage_data[-1]["day"], "%Y-%m-%d")

            # Date Range Slider
            if min_date == max_date:
                min_date -= pd.Timedelta(days=1)

            date_range = st.slider(
                "Date Range",
                min_value=min_date,
                max_value=max_date,
                value=(min_date, max_date),
                format="YYYY-MM-DD",
            )

            (
                df_usage_data_subset,
                breakdown,
                language_grouped_breakdown,
                editor_grouped_breakdown_avg,
                editor_grouped_breakdown_sum,
            ) = generate_datasets(date_range, usage_data)

            # Display Metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Suggestions", df_usage_data_subset["total_suggestions_count"].sum())
            with col2:
                st.metric("Total Accepts", df_usage_data_subset["total_acceptances_count"].sum())
            with col3:
                st.metric("Acceptance Rate", f"{round(df_usage_data_subset['acceptance_rate'].mean(), 2)}%")
            with col4:
                st.metric("Lines of Code Accepted", df_usage_data_subset["total_lines_accepted"].sum())

            # Acceptance Graph
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            fig.add_trace(
                go.Scatter(
                    mode="lines+markers+text",
                    x=df_usage_data_subset["display_day"],
                    y=df_usage_data_subset["acceptance_rate"],
                    name="Acceptance Rate (%)",
                    text=df_usage_data_subset["acceptance_rate"],
                    textposition="top center",
                ),
                secondary_y=True,
            )
            fig.add_trace(
                go.Bar(
                    x=df_usage_data_subset["display_day"],
                    y=df_usage_data_subset["total_acceptances_count"],
                    name="Acceptance Count",
                    marker_color="darkblue",
                ),
                secondary_y=False,
            )

            # Edit Layout
            fig.update_layout(
                title="Copilot Acceptance Rate",
                xaxis_title="Day",
                yaxis_title="Acceptance Count",
                yaxis2_title="Acceptance Rate (%)",
                height=600,
            )

            # Display plot in Streamlit
            st.plotly_chart(fig)

    else:
        st.error(f"Sorry, {profile['login']}, you are not part of the {org} organization.")
