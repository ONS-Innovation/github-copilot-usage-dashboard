# Streamlit Testing
A simple Streamlit app to test and learn Streamlit.

## Setup
1. Install Poetry
2. Create a virtual environment using `python3 -m venv venv`
3. Activate the virtual environment using `source venv/bin/activate`
4. Install all project dependancies using `poetry install`
5. Run the project using `streamlit run app.py`

## Data
This repository includes 2 sets of example data which mirrors the output of the Github Copilot RESTful API.
These have been sourced from [this repository](https://github.com/octodemo/Copilot-Usage-Dashboard/tree/main).
The 2 datasets are:
- copilot_usage_data.json (from [this endpoint](https://docs.github.com/en/rest/copilot/copilot-usage?apiVersion=2022-11-28#get-a-summary-of-copilot-usage-for-organization-members))
- copilot_seats_data.json (from [this enpoint](https://docs.github.com/en/rest/copilot/copilot-user-management?apiVersion=2022-11-28#list-all-copilot-seat-assignments-for-an-organization))

These endpoints are both in beta (as of 21/05/24) and may change in the future.