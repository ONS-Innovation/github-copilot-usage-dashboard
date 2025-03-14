import streamlit as st

st.logo("./src/branding/ONS_Logo_Digital_Colour_Landscape_Bilingual_RGB.svg")

col1, col2 = st.columns([0.8, 0.2])
col1.title(":blue-background[Interim Page]")
col2.image("./src/branding/ONS_Logo_Digital_Colour_Landscape_Bilingual_RGB.png")
st.write("This page serves as a temporary fix for an update in GitHub's APIs by using the new API endpoints.")

# IDE Code Completions Metrics
st.header(":blue-background[IDE Code Completions]")

# Display Metrics
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Acceptances", 0)
col2.metric("Total Suggestions", 0)
col3.metric("Total Lines of Code Suggested", 0)
col4.metric("Total Lines of Code Accepted", 0)

st.metric("Acceptance Rate", 0)

# CoPilot Chat Metrics
st.header(":blue-background[CoPilot Chat]")

# Display Metrics
col1, col2, col3 = st.columns(3)
col1.metric("Total Sessions", 0)
col2.metric("Total Insertions", 0)
col3.metric("Total Copies", 0)

col1, col2 = st.columns(2)
col1.metric("Insert Rate", 0)
col2.metric("Copy Rate", 0)

st.header(":blue-background[Seat Information]")
# TODO: Add seat information here