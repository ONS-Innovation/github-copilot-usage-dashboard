import os
from datetime import datetime
from urllib.parse import urlencode

import boto3
import github_api_toolkit
from github_api_toolkit import github_interface, github_graphql_interface
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
from plotly.subplots import make_subplots
import json

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
        "scope": "user:email read:org",
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
    return orgs.status_code == 204

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

def get_user_teams(access_token):
    """Fetch authenticated user's GitHub profile"""
    # Define the GraphQL query
    query = """
    query($login: String!, $org: String!) {
  user(login: $login) {
    organization(login: $org) {
      teams(first: 10, query: $login) {
        edges {
          node {
            name
            members(first: 10) {
              edges {
                node {
                  login
                }
              }
            }
          }
        }
      }
    }
  }
}
"""


    # Set variables for the query
    variables = {
        "login": st.session_state.profile["login"],  # Replace with the GitHub username
        "org": org  # Replace with the organization name
    }
    # return st.session_state.profile["login"]

    # Set the headers, including the authorization token
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # Make the request
    response = requests.post(
        "https://api.github.com/graphql",
        headers=headers,
        json={'query': query, 'variables': variables}
    )
    print(response.json())

    return response.text


def get_user_teams(access_token, profile):
    query = """
        query($org: String!, $name: String!) {
        organization(login: $org) {
            teams(first: 100, userLogins: [$name]) {
            totalCount
            edges {
                node {
                name
                description
                }
            }
            }
        }
        }
    """

    params={"org": org, "name": profile["login"]}
    ghql = github_api_toolkit.github_graphql_interface(access_token)

    teams = ghql.make_ql_request(query=query, params=params)
    teams_data = teams.json()
    team_names = [edge['node']['name'] for edge in teams_data['data']['organization']['teams']['edges']]
    return team_names

# # Run to get the copilot teams that are available.
# def get_copilot_teams(access_token):
#     print("Running get_copilot_teams")
#     gh = github_api_toolkit.github_interface(access_token[0])
#     for x in [1, 2]:
#         print(x)
#         teams = gh.get(f"/orgs/{org}/teams", params={"per_page": 100, "page": x})
#         teams = teams.json()
        
#         copilot_teams = []
#         for team in teams:
#             usage_data = gh.get(f"/orgs/{org}/team/{team['name']}/copilot/usage")
#             try:
#                 if usage_data.json() != []:
#                     copilot_teams.append(team['name'])
#                     print(copilot_teams)
#             except Exception as error:
#                 print(error)
    
#     if copilot_teams:
#         date_str = datetime.now().strftime("%Y-%m-%d")
#         file_path = f"./src/example_data/copilot_teams_{date_str}.json"
#         with open(file_path, "a") as file:
#             json.dump(copilot_teams, file)

# Streamlit UI starts here
st.logo("./src/branding/ONS_Logo_Digital_Colour_Landscape_Bilingual_RGB.svg")
col1, col2 = st.columns([0.8, 0.2])

# Header
col1.title(":blue-background[GitHub Team Copilot Usage]")

col2.image("./src/branding/ONS_Logo_Digital_Colour_Landscape_Bilingual_RGB.png")

# Initialize session states
if "profile" not in st.session_state:
    st.session_state.profile = None
if "slugs" not in st.session_state:
    st.session_state.slugs = []
if "oauth_token" not in st.session_state:
    st.session_state.oauth_token = None

# Step 1: GitHub Login
# If the session profile is still None,  (meaning its just been initialized) then display the login button
if st.session_state.profile is None:

    # Login button. User is directed to GitHub oauth page then once authorized they come back to this page and go to the next step
    login_url = (f"{authorize_url}?{urlencode({'client_id': client_id, 'redirect_uri': redirect_uri, 'scope': 'user:email read:org'})}")
    st.markdown(f'<a href="{login_url}" target="_self">Login with GitHub</a>', unsafe_allow_html=True)

    # Step 2: Get url params
    query_params = st.query_params
    if "code" in query_params:
        code = query_params["code"]
        try:
            # Set the session state oauth token
            st.session_state.oauth_token = get_access_token(code)
            # Get the profile of the user, to display their name and get their username for requests
            profile = get_user_profile(st.session_state.oauth_token)
            # Set the profile to the session state
            st.session_state.profile = profile
            st.query_params.clear()

        except Exception as e:
            # This would be an error with either getting the access token or getting their profile
            st.error(f"Error during login: {e}")
            st.stop()

# If the user is logged in then display the flow
if st.session_state.profile is not None:
    profile = st.session_state.profile
    st.success(f"Welcome, {profile['name']}.")

    # If user is in the org, get the access token. If not display an error and stop
    if is_user_in_org(profile["login"], org):
        access_token = get_org_access_token()
        
    else:
        st.error(f"Sorry, {profile['login']}, you are not part of the {org} organization.")
        st.stop()
    # get_copilot_teams(access_token)

    # Get the users teams
    user_teams = get_user_teams(access_token[0], profile)

    if access_token and user_teams:
        if 'keh-dev' in user_teams:

            # Add a toggle option
            input_method = st.radio("You are part of an admin team, so you can either:", ("Select your team", "Search for a team"), horizontal=True)

            if input_method == "Select your team":
                team_slug = st.selectbox("Select team:", options=user_teams)
            else:
                team_slug = st.text_input("Enter team name:", value='keh-dev')

        else:
            team_slug = st.selectbox("Select team:", options=user_teams)

        if team_slug and isinstance(access_token, tuple):
            if team_slug not in st.session_state:
                gh = github_api_toolkit.github_interface(access_token[0])
                

                
                usage_data = gh.get(f"/orgs/{org}/team/{team_slug}/copilot/usage")
                
                try:
                    usage_data = usage_data.json()
                    if usage_data:
                        st.session_state[team_slug] = usage_data
                    else:
                        st.error("Team has no data.")
                        st.stop()
                except Exception as error:
                    print(error)
                    st.error("Team does not exist.")
                    st.stop()
                    
            else:
                usage_data = st.session_state[team_slug]


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
            
            # Calculate deltas
            first_day = df_usage_data_subset.iloc[0]
            last_day = df_usage_data_subset.iloc[-1]
            
            total_suggestions_delta = ((last_day["total_suggestions_count"] - first_day["total_suggestions_count"]) / first_day["total_suggestions_count"]) * 100
            total_accepts_delta = ((last_day["total_acceptances_count"] - first_day["total_acceptances_count"]) / first_day["total_acceptances_count"]) * 100
            acceptance_rate_delta = ((last_day["acceptance_rate"] - first_day["acceptance_rate"]))
            lines_of_code_accepted_delta = ((last_day["total_lines_accepted"] - first_day["total_lines_accepted"]) / first_day["total_lines_accepted"]) * 100
            
            with col1:
                st.metric("Total Suggestions", df_usage_data_subset["total_suggestions_count"].sum(), f"{total_suggestions_delta:.2f}%")
            with col2:
                st.metric("Total Accepts", df_usage_data_subset["total_acceptances_count"].sum(), f"{total_accepts_delta:.2f}%")
            with col3:
                st.metric("Acceptance Rate", f"{round(df_usage_data_subset['acceptance_rate'].mean(), 2)}%", f"{acceptance_rate_delta:.2f}%")
            with col4:
                st.metric("Lines of Code Accepted", df_usage_data_subset["total_lines_accepted"].sum(), f"{lines_of_code_accepted_delta:.2f}%")

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
