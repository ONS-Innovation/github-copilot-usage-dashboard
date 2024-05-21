import streamlit as st
import json
import pandas as pd

st.title("Github Copilot Dashboard")

with open("example_data/copilot_usage_data.json") as f:
    data = json.load(f)

st.json(data)