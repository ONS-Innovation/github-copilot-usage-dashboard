import streamlit as st
import json
from datetime import datetime

import pandas as pd

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import boto3
from botocore.exceptions import ClientError

import api_interface

# AWS Bucket Path
bucket_name = "copilot-usage-dashboard"
object_name = "historic_usage_data.json"
file_name = "historic_usage_data.json"

# GitHub Organisation
org = "ONSdigital"

# Path to .pem file
pem = "copilot-usage-dashboard.pem"

# GitHub App Client IDß
client_id = "Iv23liRzPdnPeplrQ4x2"

st.set_page_config(layout="wide")

st.title("Github Copilot Usage Dashboard")

live_tab, historic_tab = st.tabs(["Live Data", "Historic Data"])

with live_tab:
    st.header("Live Data")

    # Get the access token
    access_token = api_interface.get_access_token(org, pem, client_id)

    use_example_data = False

    # Check if the access token is a string. If it is, then an error occurred.
    if type(access_token) == str:
        st.error("An error occurred while trying to get the access token. Please check the error message below.")
        st.error(access_token)
        st.error("Using the example dataset instead.")

        use_example_data = True

    use_example_data = st.toggle("Use Example Data", use_example_data)

    # Usage Data

    # Get a JSON version of usage data
    if use_example_data:
        with open("./src/example_data/copilot_usage_data.json") as f:
            usage_data = json.load(f)
    else:
        gh = api_interface.api_controller(access_token[0])

        usage_data = gh.get(f"/orgs/{org}/copilot/usage", params={})
        usage_data = usage_data.json()

    # Get the maximum and minimum date which we have data for from copilot_usage_data.json
    min_date = datetime.strptime(usage_data[0]["day"], "%Y-%m-%d")
    max_date = datetime.strptime(usage_data[-1]["day"], "%Y-%m-%d")

    # Create a date slider
    date_range = st.slider(
        "Date Range",
        min_value=min_date,
        max_value=max_date,
        value=(min_date, max_date),
        format="YYYY-MM-DD"
    )

    @st.cache_data
    def generate_datasets(date_range: tuple):
        """
            Converts the 2 JSON responses from the Github API into Pandas Dataframes
        """

        # Converts copilot_usage_data.json into a dataframe
        df_usage_data = pd.json_normalize(usage_data)

        # Convert date column from str to datetime
        df_usage_data["day"] = df_usage_data["day"].apply(lambda x: datetime.strptime(x, "%Y-%m-%d"))

        # Create a short version of the day
        df_usage_data["display_day"] = df_usage_data["day"].apply(lambda x: datetime.strftime(x, "%d %b"))

        # Add a column for number of ignore results
        df_usage_data["total_decline_count"] = df_usage_data.total_suggestions_count - df_usage_data.total_acceptances_count

        # Add an acceptance rate column
        df_usage_data["acceptance_rate"] = round(df_usage_data.total_acceptances_count / df_usage_data.total_suggestions_count * 100, 2)

        # Create a subset of data based on slider selection
        df_usage_data_subset = df_usage_data.loc[(df_usage_data["day"] >= date_range[0]) & (df_usage_data["day"] <= date_range[1])]


        # Breakdown Data

        breakdown = pd.DataFrame()

        # Puts df_usage_data.breakdown into a dataframe
        for i in range(0, len(df_usage_data_subset.day)):
            for d in df_usage_data_subset.breakdown[i]:
                d["day"] = df_usage_data_subset.day[i]

            breakdown = pd.concat([breakdown, pd.json_normalize(df_usage_data_subset.breakdown[i])], ignore_index=True)

        # Group the breakdown data by language
        breakdown_subset = breakdown.drop(columns=["editor", "active_users", "day"])
        language_grouped_breakdown = breakdown_subset.groupby(["language"]).sum()

        # Add acceptance_rate to language_grouped_breakdown
        language_grouped_breakdown["acceptance_rate"] = round((language_grouped_breakdown["acceptances_count"] / language_grouped_breakdown["suggestions_count"]), 2)

        # Group breakdown data by editor (IDE)
        breakdown_subset = breakdown.drop(columns=["language"])

        # Gets the average of the columns for mean active users by IDE
        editor_grouped_breakdown_avg = breakdown_subset.groupby(["editor", "day"]).mean()
        editor_grouped_breakdown_avg = editor_grouped_breakdown_avg.reset_index()

        # Gets the sum of the columns for total active users by IDE
        editor_grouped_breakdown_sum = breakdown_subset.groupby(["editor", "day"]).sum()
        editor_grouped_breakdown_sum = editor_grouped_breakdown_sum.reset_index()


        # Seat Data

        # Get a JSON version of Seat Data
        if use_example_data:
            with open("./src/example_data/copilot_seats_data.json") as f:
                seat_data = json.load(f)
        else:
            gh = api_interface.api_controller(access_token[0])

            seat_data = gh.get(f"/orgs/{org}/copilot/billing/seats", params={})
            seat_data = seat_data.json()
        

        df_seat_data = pd.DataFrame()

        # Puts the seat information from copilot_seats_data.json into a dataframe
        for row in seat_data["seats"]:
            df_seat_data = pd.concat([df_seat_data, pd.json_normalize(row)], ignore_index=True)


        def last_activity_to_datetime(use_example_data: bool, x: str | None) -> str | None:
            """
                A function used to convert the last_activity column of df_seat_data into a formatted datetime string
            """
            if use_example_data:
                if x not in (None, ""):
                    sections = x.split(":")

                    corrected_string = sections[0] + ":" + sections[1] + ":" + sections[2] + sections[3]

                    return datetime.strptime(corrected_string, "%Y-%m-%dT%H:%M:%S%z").strftime("%Y-%m-%d %H:%M")
                else:
                    return None
            else:
                if x not in (None, ""):
                    return datetime.strptime(x, "%Y-%m-%dT%H:%M:%SZ")            
                else:
                    return None

        # Converts last_activity_at to a formatted string
        df_seat_data["last_activity_at"] = df_seat_data["last_activity_at"].apply(lambda x: last_activity_to_datetime(use_example_data, x))

        return df_usage_data_subset, breakdown, language_grouped_breakdown, editor_grouped_breakdown_avg, editor_grouped_breakdown_sum, df_seat_data, seat_data


    df_usage_data_subset, breakdown, language_grouped_breakdown, editor_grouped_breakdown_avg, editor_grouped_breakdown_sum, df_seat_data, seat_data = generate_datasets(date_range)


    # Metrics for total shown, total accepts, acceptance rate and total lines accepted
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_shown = df_usage_data_subset["total_suggestions_count"].sum()
        st.metric("Total Suggestions", total_shown)
    with col2:
        total_accepts = df_usage_data_subset["total_acceptances_count"].sum()
        st.metric("Total Accepts", total_accepts)
    with col3:
        acceptance_rate = round(total_accepts / total_shown * 100, 2)
        st.metric("Acceptance Rate", str(acceptance_rate)+"%")
    with col4:
        total_lines_accepted = df_usage_data_subset["total_lines_accepted"].sum()
        st.metric("Lines of Code Accepted", total_lines_accepted)

    # Acceptance Graph

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Scatter(
            mode="lines+markers+text",
            x=df_usage_data_subset["display_day"],
            y=df_usage_data_subset["acceptance_rate"],
            name="Acceptance Rate (%)",
            text=df_usage_data_subset["acceptance_rate"],
            textposition="top center"
        ),
        secondary_y=True
    )

    fig.add_trace(
        go.Bar(
            x=df_usage_data_subset["display_day"],
            y=df_usage_data_subset["total_acceptances_count"],
            name="Total Acceptances",
            hovertext=df_usage_data_subset["total_acceptances_count"]
        )
    )

    fig.update_layout(
        title="Accepts and Acceptance Rate",
        xaxis_title="Date",
        yaxis_title="Acceptances",
        legend_title="Legend",
        hovermode="x unified"
    )

    fig.update_yaxes(title_text="Acceptance Rate (%)", secondary_y=True)

    st.plotly_chart(fig, use_container_width=True)


    # Language breakdown

    st.header("Language Breakdown")

    col1, col2 = st.columns([0.6, 0.4])

    with col1:
        language_drill = st.dataframe(
            language_grouped_breakdown[["acceptances_count", "acceptance_rate", "lines_accepted"]], 
            use_container_width=True,
            on_select="rerun",
            selection_mode=["single-row"],
            column_config={
                "acceptances_count": st.column_config.Column(
                    "Total Accepts"
                ),
                "acceptance_rate": st.column_config.ProgressColumn(
                    "Acceptance Rate",
                    help="The percentage of which Copilot suggestions are accepted",
                    min_value=0,
                    max_value=1
                ),
                "lines_accepted": st.column_config.Column(
                    "Lines of Code Accepted"
                )
            }
        )

    with col2:
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
            df_breakdown_by_day = breakdown.loc[breakdown["language"] == selected_row.index.values[0]].groupby(["day", "language", "editor"]).sum()
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
                        hovertemplate="<br>" +
                            "Number of Suggestions: %{y} <br>" +
                            "Total Suggestions for Day: %{customdata} <br>"
                    ))

            fig.update_layout(
                barmode="stack",
                title="Suggestions by Day Per Editor",
                xaxis_title="Day",
                yaxis_title="Number of Suggestions",
                hovermode="x unified",
                legend_orientation="h"
            )

            st.plotly_chart(fig)

        except IndexError:
            st.write("Please select a row for more information.")

    # User Breakdown

    st.header("User Breakdown")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Number of Seats", seat_data["total_seats"])

    with col2:
        number_of_engaged_users = 0

        for index, row in df_seat_data.iterrows():
            if pd.isnull(row.last_activity_at) == False:
                number_of_engaged_users += 1
        
        st.metric("Number of Engaged Users", number_of_engaged_users)

    with col3:
        number_of_inactive_users = seat_data["total_seats"] - number_of_engaged_users

        st.metric("Number of Inactive Users", number_of_inactive_users)


    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Active Users")

        # Dataframe showing only active users (this with a latest activity)
        st.dataframe(
            df_seat_data.loc[df_seat_data["last_activity_at"].isnull() == False][["assignee.login", "last_activity_at", "assignee.html_url"]], 
            hide_index=True, 
            use_container_width=True, 
            column_config={
                "assignee.login": st.column_config.Column(
                    "User"
                ),
                "last_activity_at": st.column_config.DatetimeColumn(
                    "Last Activity At",
                    format="YYYY-MM-DD HH:mm"
                ),
                "assignee.html_url": st.column_config.LinkColumn(
                    "Github Profile",
                    help="A link to this user's profile",
                    display_text="Go to Profile"
                )
            }
        )

    with col2:
        st.subheader("Inactive Users")

        # Dataframe showing only inactive users (those where last_activity_at is None)
        st.dataframe(
            df_seat_data.loc[df_seat_data["last_activity_at"].isnull()][["assignee.login", "last_activity_at", "assignee.html_url"]], 
            hide_index=True, 
            use_container_width=True, 
            column_config={
                "assignee.login": st.column_config.Column(
                    "User"
                ),
                "last_activity_at": st.column_config.DatetimeColumn(
                    "Last Activity At",
                    format="YYYY-MM-DD HH:mm"
                ),
                "assignee.html_url": st.column_config.LinkColumn(
                    "Github Profile",
                    help="A link to this user's profile",
                    display_text="Go to Profile"
                )
            }
        )

    # Engaged Users By Day

    fig = make_subplots()

    fig.add_trace(
        go.Bar(
            x=df_usage_data_subset["day"],
            y=df_usage_data_subset["total_active_users"]
        )
    )

    fig.update_layout(
        title="Engaged Users By Day (All Editors)",
        xaxis_title="Day",
        yaxis_title="Number of Users",
        hovermode="x unified"
    )

    st.plotly_chart(fig)

    # Engaged Users By IDE

    fig = make_subplots(
        rows=1, 
        cols=2, 
        specs=[[{"type":"pie"}, {"type":"pie"}]], 
        subplot_titles=("Average Engaged User by IDE Per Day", "Total Engaged Users by IDE")
    )

    fig.add_trace(
        go.Pie(
            values=editor_grouped_breakdown_avg["active_users"],
            labels=editor_grouped_breakdown_avg["editor"]
        ),
        row=1,
        col=1
    )

    fig.add_trace(
        go.Pie(
            values=editor_grouped_breakdown_sum["active_users"],
            labels=editor_grouped_breakdown_sum["editor"]
        ),
        row=1,
        col=2
    )

    st.plotly_chart(fig)

with historic_tab:
    st.header("Historic Data")

    date_grouping = st.radio("Organise Dates By", ["Day", "Week", "Month", "Year"])

    # Create an S3 client
    session = boto3.Session()
    s3 = session.client('s3')

    # Get historic_usage_data.json from S3
    try:
        s3.download_file(bucket_name, object_name, file_name)
    except ClientError as e:
        st.error("An error occurred while trying to get the historic data from S3. Please check the error message below.")
        st.error(e)
        st.stop()

    # Load the historic data
    with open(file_name) as f:
        historic_data = json.load(f)

    # Convert the historic data into a dataframe
    df_historic_data = pd.json_normalize(historic_data)

    # Convert date column from str to datetime
    df_historic_data["day"] = df_historic_data["day"].apply(lambda x: datetime.strptime(x, "%Y-%m-%d"))

    # Drop the breakdown column as it is unused
    df_historic_data = df_historic_data.drop(columns=["breakdown"])

    # Group the data by the date as selected by the user
    if date_grouping == "Day":
        # Format into a year-month-day format (i.e 2022-01-01)
        df_historic_data["day"] = df_historic_data["day"].dt.strftime("%Y-%m-%d")
    elif date_grouping == "Week":
        # Format into a year-week format (i.e 2022-01)
        df_historic_data["day"] = df_historic_data["day"].dt.strftime("%Y-%U")
    elif date_grouping == "Month":
        # Format into a year-month format (i.e 2022-01)
        df_historic_data["day"] = df_historic_data["day"].dt.strftime("%Y-%m")
    elif date_grouping == "Year":
        # Format into a year format (i.e 2022)
        df_historic_data["day"] = df_historic_data["day"].dt.strftime("%Y")

    # Group the data by the date
    df_historic_data = df_historic_data.groupby(["day"]).sum()
    df_historic_data = df_historic_data.reset_index()

    # st.dataframe(df_historic_data, use_container_width=True)

    # Add a column for the acceptance rate
    df_historic_data["acceptance_rate"] = round(df_historic_data["total_acceptances_count"] / df_historic_data["total_suggestions_count"] * 100, 2)

    # Acceptance Graph

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Scatter(
            mode="lines+markers+text",
            x=df_historic_data["day"],
            y=df_historic_data["acceptance_rate"],
            name="Acceptance Rate (%)",
            text=df_historic_data["acceptance_rate"],
            textposition="top center"
        ),
        secondary_y=True
    )

    fig.add_trace(
        go.Bar(
            x=df_historic_data["day"],
            y=df_historic_data["total_acceptances_count"],
            name="Total Acceptances",
            hovertext=df_historic_data["total_acceptances_count"]
        )
    )

    fig.update_layout(
        title="Accepts and Acceptance Rate",
        xaxis_title="Date",
        yaxis_title="Acceptances",
        legend_title="Legend",
        hovermode="x unified"
    )

    fig.update_yaxes(title_text="Acceptance Rate (%)", secondary_y=True)
    fig.update_xaxes(type="category")

    st.plotly_chart(fig, use_container_width=True)

    # Engaged Users By Day

    fig = make_subplots()

    fig.add_trace(
        go.Bar(
            x=df_historic_data["day"],
            y=df_historic_data["total_active_users"]
        )
    )

    fig.update_layout(
        title="Engaged Users By Day (All Editors)",
        xaxis_title="Day",
        yaxis_title="Number of Users",
        hovermode="x unified"
    )

    fig.update_xaxes(type="category")

    st.plotly_chart(fig)