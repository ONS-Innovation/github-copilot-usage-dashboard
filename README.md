# Streamlit Testing
A Streamlit dashboard to display information from the Github Copilot Usage API endpoints.

## Setup
1. Install Poetry
2. Create a virtual environment using `python3 -m venv venv`
3. Activate the virtual environment using `source venv/bin/activate`
4. Install all project dependancies using `poetry install`
5. Run the project using `streamlit run src/app.py`

## Data
### Example Data
This repository includes 2 sets of example data which mirrors the output of the Github Copilot RESTful API.
These have been sourced from [this repository](https://github.com/octodemo/Copilot-Usage-Dashboard/tree/main).
The 2 datasets are:
- copilot_usage_data.json (from [this endpoint](https://docs.github.com/en/rest/copilot/copilot-usage?apiVersion=2022-11-28#get-a-summary-of-copilot-usage-for-organization-members))
- copilot_seats_data.json (from [this enpoint](https://docs.github.com/en/rest/copilot/copilot-user-management?apiVersion=2022-11-28#list-all-copilot-seat-assignments-for-an-organization))

These endpoints are both in beta (as of 21/05/24) and may change in the future.

## Streamlit and Supporting Libraries
This project uses [Streamlit](https://streamlit.io/) to build a quick and easy web app. Streamlit can generate front ends without the need for any HTML, CSS or JS. This means that the dashboard can be more quickly than alternative frameworks such as [Dash](https://dash.plotly.com/) which is similar to a [Flask](https://flask.palletsprojects.com/en/3.0.x/) app. Streamlit also supports the use of many other libraries. For example, Streamlit can render many graphing libraries, such as Matplotlib, Altair and Plotly. 

In this project, [Plotly](https://plotly.com/python/) is used alongside [Pandas](https://pandas.pydata.org/docs/index.html) to create visualisations from the API data. Plotly was chosen because of its interactivity while still allowing for a range of technical visualisations.