import streamlit as st
import json
from datetime import datetime

import pandas as pd

# import matplotlib.pyplot as plt
# import matplotlib.ticker as ticker

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(layout="wide")

st.title("Github Copilot Dashboard")

# Usage Data

with open("./src/example_data/copilot_usage_data.json") as f:
    usage_data = json.load(f)

df_usage_data = pd.read_json("./src/example_data/copilot_usage_data.json")
# df_usage_data = pd.read_json("./src/example_data/copilot_usage_data.json").drop(columns="breakdown")

# Convert date column from str to datetime
df_usage_data["day"] = df_usage_data["day"].apply(lambda x: datetime.strptime(x, "%Y-%m-%d"))

# Create a short version of the day
df_usage_data["display_day"] = df_usage_data["day"].apply(lambda x: datetime.strftime(x, "%d %b"))

# Add a column for number of ignore results
df_usage_data["total_decline_count"] = df_usage_data.total_suggestions_count - df_usage_data.total_acceptances_count

# Add an acceptance rate column
df_usage_data["acceptance_rate"] = round(df_usage_data.total_acceptances_count / df_usage_data.total_suggestions_count * 100, 2)


# Breakdown Data

breakdown = pd.DataFrame()

for row in df_usage_data.breakdown:
    breakdown = pd.concat([breakdown, pd.json_normalize(row)], ignore_index=True)

grouped_breakdown = breakdown.groupby(["language"]).sum().drop(columns=["editor", "active_users"])

# Add acceptance_rate to grouped_breakdown
grouped_breakdown["acceptance_rate"] = round((grouped_breakdown["acceptances_count"] / grouped_breakdown["suggestions_count"]), 2)


# Seat Data

with open("./src/example_data/copilot_seats_data.json") as f:
    seat_data = json.load(f)

df_seat_data = pd.DataFrame()

for row in seat_data["seats"]:
    df_seat_data = pd.concat([df_seat_data, pd.json_normalize(row)], ignore_index=True)

def last_activity_to_datetime(x: str | None) -> datetime | None:
    if x not in (None, ""):
        sections = x.split(":")

        corrected_string = sections[0] + ":" + sections[1] + ":" + sections[2] + sections[3]

        return datetime.strptime(corrected_string, "%Y-%m-%dT%H:%M:%S%z").strftime("%Y-%m-%d %H:%M")
    else:
        return None

df_seat_data["last_activity_at"] = df_seat_data["last_activity_at"].apply(lambda x: last_activity_to_datetime(x))


min_date = datetime.strptime(usage_data[0]["day"], "%Y-%m-%d")
max_date = datetime.strptime(usage_data[-1]["day"], "%Y-%m-%d")

date_range = st.slider(
    "Date Range",
    min_value=min_date,
    max_value=max_date,
    value=(min_date, max_date),
    format="YYYY-MM-DD"
)

# Create a subset of data based on slider selection
data_subset = df_usage_data.loc[(df_usage_data["day"] >= date_range[0]) & (df_usage_data["day"] <= date_range[1])]

# Metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    total_shown = data_subset["total_suggestions_count"].sum()
    st.metric("Total Suggestions", total_shown)
with col2:
    total_accepts = data_subset["total_acceptances_count"].sum()
    st.metric("Total Accepts", total_accepts)
with col3:
    acceptance_rate = round(total_accepts / total_shown * 100, 2)
    st.metric("Acceptance Rate", str(acceptance_rate)+"%")
with col4:
    total_lines_accepted = data_subset["total_lines_accepted"].sum()
    st.metric("Lines of Code Accepted", total_lines_accepted)

# Acceptance Graph

# # Combined Bar and Line Graph (Matplotlib)
# fig, ax = plt.subplots()

# data["total_acceptances_count"].plot(kind="bar", label="Total Acceptances")
# data["acceptance_rate"].plot(secondary_y=True, color="red", label="Acceptance Rate (%)")

# ax = plt.gca()
# ax.set_xticklabels(data["display_day"])
# ax.xaxis.set_major_locator(ticker.MultipleLocator(2))
# fig.autofmt_xdate()

# plt.legend()

# st.pyplot(fig)


# # Native Streamlit Plotting (Very Basic)
# st.bar_chart(data, x="display_day", y="total_acceptances_count")
# st.line_chart(data, x="display_day", y="acceptance_rate")


# Plotly

# #Plotly Express Bar chart
# fig = px.bar(
#     data_subset, 
#     x="display_day", 
#     y=["total_acceptances_count", "total_decline_count"], 
#     title="Number of Acceptances and Declines",
#     text_auto=True)

fig = make_subplots(specs=[[{"secondary_y": True}]])

fig.add_trace(
    go.Scatter(
        mode="lines+markers+text",
        x=data_subset["display_day"],
        y=data_subset["acceptance_rate"],
        name="Acceptance Rate (%)",
        text=data_subset["acceptance_rate"],
        textposition="top center"
    ),
    secondary_y=True
)

fig.add_trace(
    go.Bar(
        x=data_subset["display_day"],
        y=data_subset["total_acceptances_count"],
        name="Total Acceptances",
        hovertext=data_subset["total_acceptances_count"]
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


col1, col2 = st.columns([0.6, 0.4])

with col1:
    st.header("User Breakdown")


    st.subheader("Active Users")

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

    st.subheader("Inactive Users")

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


with col2:
    st.header("Language Breakdown")

    language_drill = st.dataframe(
        grouped_breakdown[["acceptances_count", "acceptance_rate", "lines_accepted"]], 
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

    try:
        selected_row = grouped_breakdown.iloc[[language_drill.selection["rows"][0]]]

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

    except IndexError:
        st.write("Please select a row for more information.")

col1, col2, col3 = st.columns([0.2, 0.4, 0.4])

with col1:
    st.metric("Number of Seats", seat_data["total_seats"])

    number_of_engaged_users = 0

    for index, row in df_seat_data.iterrows():
        if row.last_activity_at not in (None, ""):
            number_of_engaged_users += 1
    
    st.metric("Number of Engaged Users", number_of_engaged_users)

with col2:
    st.write("yippee")

with col3:
    st.write("yippee")