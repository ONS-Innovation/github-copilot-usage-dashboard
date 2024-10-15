import streamlit as st

st.set_page_config(
    page_title="CoPilot Usage Dashboard",
    page_icon="./src/branding/ONS-symbol_digital.svg",
    layout="wide",
)
org_usage = st.Page("./pages/org_usage.py", title="Organization Usage", icon=":material/groups:")
team_usage = st.Page("./pages/team_usage.py", title="Team Usage", icon=":material/group:")

pg = st.navigation([org_usage, team_usage])
pg.run()