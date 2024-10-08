import json
import os
from datetime import datetime
from urllib.parse import urlencode

import boto3
import github_api_toolkit
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
from botocore.exceptions import ClientError
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

bucket_name = "copilot-usage-dashboard"
object_name = "admin_teams.json"

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


def get_user_profile(oauth_token):
    """Fetch authenticated user's GitHub profile"""
    headers = {"Authorization": f"token {oauth_token}"}
    response = requests.get(user_api_url, headers=headers)
    response.raise_for_status()
    return response.json()


def is_user_in_org(username, org):
    """
    Check if a user is a member of a specified GitHub organization.
    Args:
        username (str): The GitHub username to check.
        org (str): The GitHub organization name.
    Returns:
        bool: True if the user is a member of the organization, False otherwise.
    """
    orgs = gh.get(f"/orgs/{org}/members/{username}")
    return orgs.status_code == 204

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


def get_user_teams(access_token, profile):
    """Fetches the list of team names that a user belongs to within a specified GitHub organization.
        Args:
            access_token (str): The GitHub access token for authentication.
            profile (dict): The user's profile information containing at least the 'login' key.
        Returns:
            list: A list of team names that the user belongs to within the organization.
    """
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

    params = {"org": org, "name": profile["login"]}
    ghql = github_api_toolkit.github_graphql_interface(access_token)

    teams = ghql.make_ql_request(query=query, params=params)
    teams_data = teams.json()
    team_names = [edge["node"]["name"] for edge in teams_data["data"]["organization"]["teams"]["edges"]]
    return team_names


# # Run to get the copilot teams that are available.
# def get_copilot_teams(access_token):
#     print("Running get_copilot_teams")
#     gh = github_api_toolkit.github_interface(access_token[0])
#     copilot_teams = []

#     for x in [1, 2]:
#         print(x)
#         teams = gh.get(f"/orgs/{org}/teams", params={"per_page": 100, "page": x})
#         teams = teams.json()
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


def get_team_seats(access_token, team):
    """
    Retrieves and filters GitHub Copilot seat data for a specific team within an organization.
    Args:
        access_token (str): The GitHub access token for authentication.
        team (str): The name of the team within the organization.
    Returns:
        pandas.DataFrame: A DataFrame containing the filtered seat data for the specified team.
    """

    seat_data = gh.get(f"/orgs/{org}/copilot/billing/seats", params={"per_page": 100})
    seat_data = seat_data.json()

    df_seat_data = pd.DataFrame()

    # Puts the seat information from copilot_seats_data.json into a dataframe
    for row in seat_data["seats"]:
        df_seat_data = pd.concat([df_seat_data, pd.json_normalize(row)], ignore_index=True)

    # Filter the dataframe to include only the rows where the team matches
    # Get the members of the team
    team_members_response = gh.get(f"/orgs/{org}/teams/{team}/members")
    team_members = team_members_response.json()
    team_member_logins = [member["login"] for member in team_members]

    # Filter the dataframe to include only the rows where the team matches and the user is in the team
    df_team_seat_data = df_seat_data[df_seat_data["assignee.login"].isin(team_member_logins)]

    return df_team_seat_data

def initialize_states():
    # Initialize session states
    if "profile" not in st.session_state:
        st.session_state.profile = None
    if "slugs" not in st.session_state:
        st.session_state.slugs = []
    if "oauth_token" not in st.session_state:
        st.session_state.oauth_token = None

# Streamlit UI starts here
st.logo("./src/branding/ONS_Logo_Digital_Colour_Landscape_Bilingual_RGB.svg")
col1, col2 = st.columns([0.8, 0.2])

# Header
col1.title(":blue-background[GitHub Team Copilot Usage]")

col2.image("./src/branding/ONS_Logo_Digital_Colour_Landscape_Bilingual_RGB.png")

initialize_states()

# Step 1: GitHub Login
# If the session profile is still None,  (meaning its just been initialized) then display the login button
if st.session_state.profile is None:

    # Step 2: Get url params
    if "code" in st.query_params:
        code = st.query_params["code"]
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
    else:
        # Login button. User is directed to GitHub oauth page then once authorized they come back to this page and go to the next step
        login_url = f"{authorize_url}?{urlencode({'client_id': client_id, 'redirect_uri': redirect_uri, 'scope': 'user:email read:org'})}"
        st.markdown(
            f'<a href="{login_url}" target="_self">:blue-background[Login with GitHub]</a>', unsafe_allow_html=True
        )


# If the user is logged in then display the flow
if st.session_state.profile:


    col1, col2 = st.columns([0.4, 0.6])
    with col1:
        st.success(f"Welcome, {st.session_state.profile['name']}.")
    with col2:
        st.info(
            "A GitHub team must have a minumum of 5 members with active CoPilot licenses for at least 1 day to display usage data."
        )

    # If user is in the org, get the access token. If not display an error and stop
    if not is_user_in_org(st.session_state.profile["login"], org):
        st.error(f"Sorry, {st.session_state.profile['login']}, you are not part of the {org} organization.")
        st.stop()

    # Get the users teams
    user_teams = get_user_teams(access_token[0], st.session_state.profile)

    if access_token and user_teams:
        # Get admin_teams.json from S3
        try:
            response = s3.get_object(Bucket=bucket_name, Key=object_name)
            admin_teams = json.loads(response["Body"].read().decode("utf-8"))

        except ClientError as e:
            st.error(
                f"An error occurred while trying to get the historic data from S3 ({object_name}). Please check the error message below."
            )
            st.error(e)
            st.stop()

        if any(admin_team in user_teams for admin_team in admin_teams):
            # Add a toggle option
            input_method = st.radio(
                "You are part of an admin team, so you can either:",
                ("Select your team", "Search for a team"),
                horizontal=True,
            )

            if input_method == "Select your team":
                team_slug = st.selectbox("Select team:", options=user_teams)
            else:
                team_slug = st.text_input("Enter team name:", value="keh-dev")

        else:
            team_slug = st.selectbox("Select team:", options=user_teams)

        if team_slug and isinstance(access_token, tuple):
            if team_slug not in st.session_state:
                usage_data = gh.get(f"/orgs/{org}/team/{team_slug}/copilot/usage")
                # Get the team description
                try:
                    team_info = gh.get(f"/orgs/{org}/teams/{team_slug}")
                    team_info = team_info.json()
                    team_description = team_info.get("description")
                    if team_description == "":
                        team_description = "No description available."
                    st.session_state[f"{team_slug}-description"] = team_description
                except:
                    st.error("Team does not exist.")
                    st.stop()

                try:
                    usage_data = usage_data.json()
                    if usage_data:
                        st.session_state[team_slug] = usage_data
                    else:
                        st.error("Team has no data.")
                        st.stop()
                except Exception:
                    st.error("Team does not exist.")
                    st.stop()

            else:
                usage_data = st.session_state[team_slug]

            st.markdown("---")

            st.subheader(f"Team: {team_slug}")
            description = st.session_state.get(f"{team_slug}-description")
            st.write(description)

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

            total_suggestions_delta = (
                (last_day["total_suggestions_count"] - first_day["total_suggestions_count"])
                / first_day["total_suggestions_count"]
            ) * 100
            total_accepts_delta = (
                (last_day["total_acceptances_count"] - first_day["total_acceptances_count"])
                / first_day["total_acceptances_count"]
            ) * 100
            acceptance_rate_delta = last_day["acceptance_rate"] - first_day["acceptance_rate"]
            lines_of_code_accepted_delta = (
                (last_day["total_lines_accepted"] - first_day["total_lines_accepted"])
                / first_day["total_lines_accepted"]
            ) * 100

            with col1:
                st.metric(
                    "Total Suggestions",
                    df_usage_data_subset["total_suggestions_count"].sum(),
                    f"{total_suggestions_delta:.2f}%",
                )
            with col2:
                st.metric(
                    "Total Accepts",
                    df_usage_data_subset["total_acceptances_count"].sum(),
                    f"{total_accepts_delta:.2f}%",
                )
            with col3:
                st.metric(
                    "Acceptance Rate",
                    f"{round(df_usage_data_subset['acceptance_rate'].mean(), 2)}%",
                    f"{acceptance_rate_delta:.2f}%",
                )
            with col4:
                st.metric(
                    "Lines of Code Accepted",
                    df_usage_data_subset["total_lines_accepted"].sum(),
                    f"{lines_of_code_accepted_delta:.2f}%",
                )

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
                ),
                secondary_y=False,
            )

            # Edit Layout
            fig.update_layout(
                title="Accepts and Acceptance Rate",
                xaxis_title="Day",
                yaxis_title="Acceptance Count",
                yaxis2_title="Acceptance Rate (%)",
                height=600,
            )

            # Display plot in Streamlit
            st.plotly_chart(fig)

        # Language breakdown

        st.header(":blue-background[Language Breakdown]")

        language_drill = st.dataframe(
            language_grouped_breakdown[["acceptances_count", "acceptance_rate", "lines_accepted"]],
            use_container_width=True,
            on_select="rerun",
            selection_mode=["single-row"],
            column_config={
                "acceptances_count": st.column_config.Column("Total Accepts"),
                "acceptance_rate": st.column_config.ProgressColumn(
                    "Acceptance Rate",
                    help="The percentage of which Copilot suggestions are accepted",
                    min_value=0,
                    max_value=1,
                ),
                "lines_accepted": st.column_config.Column("Lines of Code Accepted"),
            },
        )

        # Extra Drill through information. Only shows when a row is selected from language_drill dataframe above
        try:
            selected_row = language_grouped_breakdown.iloc[[language_drill.selection["rows"][0]]]

            col1, col2, col3, col4, col5 = st.columns(5)

            with col1:
                st.metric("Language", selected_row.index.values[0])
            with col2:
                st.metric("Total Suggestions", selected_row["suggestions_count"])
            with col3:
                st.metric("Total Accepts", selected_row["acceptances_count"])
            with col4:
                st.metric("Lines Suggested", selected_row["lines_suggested"])
            with col5:
                st.metric("Lines Accepted", selected_row["lines_accepted"])

            # Creates a subset of breakdown dataframe to only hold information for the selected language
            df_breakdown_by_day = (
                breakdown.loc[breakdown["language"] == selected_row.index.values[0]]
                .groupby(["day", "language", "editor"])
                .sum()
            )
            df_breakdown_by_day = df_breakdown_by_day.reset_index()

            # Calculates the total copilot suggestion for the date
            df_date_totals = df_breakdown_by_day[["day", "suggestions_count"]].groupby(["day"]).sum()
            df_date_totals = df_date_totals.rename(columns={"suggestions_count": "total_suggestions"})
            df_date_totals = df_date_totals.reset_index()

            # Merges df_date_totals into df_breakdown_by_day. This adds the total_suggestions column for each record
            df_breakdown_by_day = df_breakdown_by_day.merge(df_date_totals, on="day", how="left")

            # Create a graph showing number of suggestions by day, split by IDE.
            fig = make_subplots()

            list_of_editors = df_breakdown_by_day["editor"].unique()

            for editor in list_of_editors:
                df = df_breakdown_by_day.loc[df_breakdown_by_day["editor"] == editor]

                fig.add_trace(
                    go.Bar(
                        name=editor,
                        x=df["day"],
                        y=df["suggestions_count"],
                        customdata=df["total_suggestions"],
                        hovertemplate="<br>"
                        + "Number of Suggestions: %{y} <br>"
                        + "Total Suggestions for Day: %{customdata} <br>",
                    )
                )

            fig.update_layout(
                barmode="stack",
                title="Suggestions by Day Per Editor",
                xaxis_title="Day",
                yaxis_title="Number of Suggestions",
                hovermode="x unified",
                legend_orientation="h",
            )

            st.plotly_chart(fig)

        except IndexError:
            st.caption("Please select a row for more information.")

        # User Breakdown

        df_seat_data = get_team_seats(access_token, team_slug)

        st.header(":blue-background[User Breakdown]")
        st.write(
            "Active users have used CoPilot within the last 30 days. Inactive users have not used CoPilot within the last 30 days or have not used CoPilot yet."
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Number of Seats", len(df_seat_data))

        with col2:
            number_of_engaged_users = 0

            df_unused_users = pd.DataFrame(
                columns=["assignee.avatar_url", "assignee.login", "last_activity_at", "assignee.html_url"]
            )

            for index, row in df_seat_data.iterrows():
                if pd.isnull(row.last_activity_at) == False:
                    last_activity_date = datetime.strptime(row.last_activity_at, "%Y-%m-%dT%H:%M:%SZ")
                    if (datetime.now() - last_activity_date).days <= 30:
                        number_of_engaged_users += 1
                    else:
                        df_unused_users = pd.concat([df_unused_users, pd.DataFrame([row])], ignore_index=True)
                        df_seat_data.drop(index, inplace=True)
                else:
                    df_unused_users = pd.concat([df_unused_users, pd.DataFrame([row])], ignore_index=True)
                    df_seat_data.drop(index, inplace=True)

            st.metric("Number of Engaged Users", number_of_engaged_users)
        with col3:
            st.metric("Number of Inactive Users", len(df_unused_users))

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Active Users")

            # Dataframe showing only active users (this with a latest activity)
            st.dataframe(
                df_seat_data.loc[df_seat_data["last_activity_at"].isnull() == False][
                    ["assignee.avatar_url", "assignee.login", "last_activity_at", "assignee.html_url"]
                ],
                hide_index=True,
                use_container_width=True,
                column_config={
                    "assignee.avatar_url": st.column_config.ImageColumn("Avatar", width=10),
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

            # Dataframe showing inactive users (users with no latest activity or not within a month)
            st.dataframe(
                df_unused_users[["assignee.avatar_url", "assignee.login", "last_activity_at", "assignee.html_url"]],
                hide_index=True,
                use_container_width=True,
                column_config={
                    "assignee.avatar_url": st.column_config.ImageColumn("Avatar", width=10),
                    "assignee.login": st.column_config.Column("User"),
                    "last_activity_at": st.column_config.DatetimeColumn("Last Activity At", format="YYYY-MM-DD HH:mm"),
                    "assignee.html_url": st.column_config.LinkColumn(
                        "Github Profile",
                        help="A link to this user's profile",
                        display_text="Go to Profile",
                    ),
                },
            )

        # Engaged Users By Day

        fig = make_subplots()

        fig.add_trace(go.Bar(x=df_usage_data_subset["day"], y=df_usage_data_subset["total_active_users"]))

        fig.update_layout(
            title="Engaged Users By Day (All Editors)",
            xaxis_title="Day",
            yaxis_title="Number of Users",
            hovermode="x unified",
        )

        st.plotly_chart(fig)

        # Engaged Users By IDE

        fig = make_subplots(
            rows=1,
            cols=2,
            specs=[[{"type": "pie"}, {"type": "pie"}]],
            subplot_titles=(
                "Average Engaged User by IDE Per Day",
                "Total Engaged Users by IDE",
            ),
        )

        fig.add_trace(
            go.Pie(
                values=editor_grouped_breakdown_avg["active_users"],
                labels=editor_grouped_breakdown_avg["editor"],
            ),
            row=1,
            col=1,
        )

        fig.add_trace(
            go.Pie(
                values=editor_grouped_breakdown_sum["active_users"],
                labels=editor_grouped_breakdown_sum["editor"],
            ),
            row=1,
            col=2,
        )

        st.plotly_chart(fig)

    else:
        st.error(f"Sorry, {st.session_state.profile['login']}, you are not part of the {org} organization.")
