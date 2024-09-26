import streamlit as st

st.set_page_config(
    page_title="CoPilot Usage Dashboard",
    page_icon="./src/branding/ONS-symbol_digital.svg",
    layout="wide",
)
create_page = st.Page("./pages/org_usage.py", title="Organization Usage", icon=":material/groups:")
delete_page = st.Page("./pages/team_usage.py", title="Team Usage", icon=":material/group:")

pg = st.navigation([create_page, delete_page])
pg.run()