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

df_usage_data = pd.read_json("./src/example_data/copilot_usage_data.json").drop(columns="breakdown")

# Convert date column from str to datetime
df_usage_data["day"] = df_usage_data["day"].apply(lambda x: datetime.strptime(x, "%Y-%m-%d"))

# Create a short version of the day
df_usage_data["display_day"] = df_usage_data["day"].apply(lambda x: datetime.strftime(x, "%d %b"))

# Add a column for number of ignore results
df_usage_data["total_decline_count"] = df_usage_data.total_suggestions_count - df_usage_data.total_acceptances_count

# Add an acceptance rate column
df_usage_data["acceptance_rate"] = round(df_usage_data.total_acceptances_count / df_usage_data.total_suggestions_count * 100, 2)


# Breakdown Data

# breakdown = pd.DataFrame()

# for row in summaryData.breakdown:
#     breakdown = pd.concat([breakdown, pd.json_normalize(row)])

# breakdown = breakdown.groupby(["language", "editor"]).sum()

# st.dataframe(summaryData, column_config={"breakdown": None})

# st.dataframe(breakdown)


# Seat Data

with open("./src/example_data/copilot_seats_data.json") as f:
    seat_data = json.load(f)

df_seat_data = pd.DataFrame()

for row in seat_data["seats"]:
    df_seat_data = pd.concat([df_seat_data, pd.json_normalize(row)])

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
    st.metric("Total Shown", total_shown)
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
    go.Bar(
        x=data_subset["display_day"],
        y=data_subset["total_acceptances_count"],
        name="Total Acceptances",
        hovertext=data_subset["total_acceptances_count"]
    )
)

fig.add_trace(
    go.Scatter(
        mode="lines+markers+text",
        x=data_subset["display_day"],
        y=data_subset["acceptance_rate"],
        name="Acceptance Rate (%)",
        text=data_subset["acceptance_rate"],
        textposition="top center",
        textfont={
            "color": "white"
        }
    ),
    secondary_y=True
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


col1, col2 = st.columns([0.7, 0.3])

with col1:
    st.dataframe(df_seat_data)

with col2:
    st.write("WOOOOO!")