# Streamlit Testing
A Streamlit dashboard to display information from the Github Copilot Usage API endpoints.

## Prerequisites
This project uses poetry for package management.

[Instructions to install Poetry](https://python-poetry.org/docs/)

## Setup - Run outside of Docker
1. Navigate into the project's folder and create a virtual environment using `python3 -m venv venv`
2. Activate the virtual environment using `source venv/bin/activate`
3. Install all project dependancies using `poetry install`
4. Get the copilot-usage-dashboard.pem and copy to the source code root directory (see "Getting a .pem file" below).
5. Run the project using `streamlit run src/app.py`

## Setup - Running in a container
TODO

## Data
### Example Data
This repository includes 2 sets of example data which mirrors the output of the Github Copilot RESTful API.
These have been sourced from [this repository](https://github.com/octodemo/Copilot-Usage-Dashboard/tree/main).
The 2 datasets are:
- copilot_usage_data.json (from [this endpoint](https://docs.github.com/en/rest/copilot/copilot-usage?apiVersion=2022-11-28#get-a-summary-of-copilot-usage-for-organization-members))
- copilot_seats_data.json (from [this enpoint](https://docs.github.com/en/rest/copilot/copilot-user-management?apiVersion=2022-11-28#list-all-copilot-seat-assignments-for-an-organization))

These endpoints are both in beta (as of 21/05/24) and may change in the future.

### Live Data
To use real data from the Github API, the project must be supplied with a copilot-usage-dashboard.pem file.

#### Getting a .pem file for the Github App

A .pem file is used to allow the project to make authorised Github API requests through the means of Github App authentication.
The project uses authentication as a Github App installation ([documentation](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/authenticating-as-a-github-app-installation)).

In order to get a .pem file, a Github App must be created an installed into the organisation of which the app will be managing.
This app should have **Read and Write Administration** organisation permission and **Read-only GitHub Copilot Business** organisation permission.

Once created and installed, you need to generate a Private Key for that Github App. This will download a .pem file to your pc.
This file needs to be renamed **copilot-usage-dashboard.pem** ([documentation](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/managing-private-keys-for-github-apps)).

If you do not have access to organisation settings, you need to request a .pem file for the app.

## Streamlit and Supporting Libraries
This project uses [Streamlit](https://streamlit.io/) to build a quick and easy web app. Streamlit can generate front ends without the need for any HTML, CSS or JS. This means that the dashboard can be more quickly than alternative frameworks such as [Dash](https://dash.plotly.com/) which is similar to a [Flask](https://flask.palletsprojects.com/en/3.0.x/) app. Streamlit also supports the use of many other libraries. For example, Streamlit can render many graphing libraries, such as Matplotlib, Altair and Plotly. 

In this project, [Plotly](https://plotly.com/python/) is used alongside [Pandas](https://pandas.pydata.org/docs/index.html) to create visualisations from the API data. Plotly was chosen because of its interactivity while still allowing for a range of technical visualisations.