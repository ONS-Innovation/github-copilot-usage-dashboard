import streamlit as st
import json
import pandas as pd
from datetime import datetime

st.title("Github Copilot Dashboard")

with open("./src/example_data/copilot_seats_data.json") as f:
    seat_data = json.load(f)

with open("./src/example_data/copilot_usage_data.json") as f:
    usage_data = json.load(f)

# st.json(usage_data)

data = pd.read_json("./src/example_data/copilot_usage_data.json").drop(columns="breakdown")

data["day"] = data["day"].apply(lambda x: datetime.strptime(x, "%Y-%m-%d"))

# breakdown = pd.DataFrame()

# for row in summaryData.breakdown:
#     breakdown = pd.concat([breakdown, pd.json_normalize(row)])

# breakdown = breakdown.groupby(["language", "editor"]).sum()

# st.dataframe(summaryData, column_config={"breakdown": None})

# st.dataframe(breakdown)


min_date = datetime.strptime(usage_data[0]["day"], "%Y-%m-%d")
max_date = datetime.strptime(usage_data[-1]["day"], "%Y-%m-%d")

date_range = st.slider(
    "Date Range",
    min_value=min_date,
    max_value=max_date,
    value=(min_date, max_date),
    format="YYYY-MM-DD"
)


col1, col2, col3, col4 = st.columns(4)

total_shown = data.loc[(data["day"] >= date_range[0]) & (data["day"] <= date_range[1])]["total_suggestions_count"].sum()
total_accepts = data.loc[(data["day"] >= date_range[0]) & (data["day"] <= date_range[1])]["total_acceptances_count"].sum()
acceptance_rate = round(total_accepts / total_shown * 100, 2)
total_lines_accepted = data.loc[(data["day"] >= date_range[0]) & (data["day"] <= date_range[1])]["total_lines_accepted"].sum()

col1.metric("Total Shown", total_shown)
col2.metric("Total Accepts", total_accepts)
col3.metric("Acceptance Rate", str(acceptance_rate)+"%")
col4.metric("Lines of Code Accepted", total_lines_accepted)
