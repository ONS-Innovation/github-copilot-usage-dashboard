# GitHub Copilot Usage Dashboard

## Overview

This project contains a dashboard which displays ONSDigital's GitHub CoPilot usage metrics via the GitHub RESTful API. The dashboard is written in Python and uses [Streamlit](https://streamlit.io/) to produce a quick, easy and responsive UI. This project also makes use of a library called [Plotly](https://plotly.com/python/) to produce high quality and interactive graphs.

**Please Note:** This project is a Proof of concept and may not comply with Civil Service/ONS best practices. This tool is only being used by a limited number of users.

## Techstack Overview
### Streamlit

[Streamlit](https://streamlit.io/) is a powerful web framework which promotes creating apps quickly and without the need of any frontend writing. This makes Streamlit well suited to the project due to the speed of development and heavy data focus. Streamlit also promotes interactivity within its apps which is crucial when making a dashboard as you want users to be able to play with the data to get the most from it. This project has been used as a proof of concept for Streamlit, testing its capabilities and potential for future projects. A small drawback is Streamlit's potential lack of accessibility. This project hasn't been accessibility tested but, due to its limited target audience, is still fit for purpose. Another limitation of the tool is its ability to be customised to look and feel like an ONS product. Streamlit offers customisation within its colour scheme and allows logos to be added, however it will still look like a Streamlit application.

### Plotly

[Plotly](https://plotly.com/python/) is a graphing library used within the project. Plotly was chosen because of its high interactivity, ability to export and general ease of use alongside Streamlit. Other libraries, such as Matplotlib, were trialed alongside Plotly during early development. It was found that Plotly just generally suited Streamlit's feel and focus on interactivity, which is why it was chosen. Another advantage of Plotly was its incorporation with [Dash](https://dash.plotly.com/), a dashboarding tool built on top of the Flask framework. This means that if Dash was to be used in the future (perhaps to onboard a dashboard onto the ONS Design System), we'd already have some knowledge on how to use it.

## Architecture Overview

![Architecture Diagram](./diagrams/architecture.png)

This project uses 3 major components:

- The Dashboard
- The Lambda Function
- The GitHub API Toolkit (**stored in another repository** - [Repository Link](https://github.com/ONS-Innovation/github-api-package))

### The Dashboard

This component is responsible for displaying data back to the user. The dashboard gathers live data from the GitHub API using the API Toolkit. If this process fails, it will display the example dataset (stored within ./src/example_data) instead. The dashboard also gathers the historic data from an S3 bucket.

### The Lambda Function

This component updates the dashboard's historic information, stored within an S3 bucket. The lambda imports the GitHub API Toolkit to get the API response containing the usage information. The script then adds any new data to the existing historic data within the S3 bucket.

### The GitHub API Toolkit

This component is an imported library which is shared across multiple GitHub tools. The toolkit allows applications to make authenticated requests to the GitHub API. It is imported and used by both the dashboard and lambda function.

## High Level Data Overview
### Live Data

The data used within this section of the tool is pulled directly from the GitHub API at runtime. This data is dependant on a GitHub App being setup within the target organisation, with the correct permissions (as outlined in the [README](https://github.com/ONS-Innovation/github-copilot-usage-dashboard/blob/master/README.md)).

### Example Data

In the event that the dashboard cannot access live data from the GitHub API, the dashboard has an example dataset stored within the repository. These have been sourced from [this repository](https://github.com/octodemo/Copilot-Usage-Dashboard/tree/main). The datasets mirror the response which an API call would make.

The 2 datasets are:

- copilot_usage_data.json (from [this endpoint](https://docs.github.com/en/rest/copilot/copilot-usage?apiVersion=2022-11-28#get-a-summary-of-copilot-usage-for-organization-members))
- copilot_seats_data.json (from [this enpoint](https://docs.github.com/en/rest/copilot/copilot-user-management?apiVersion=2022-11-28#list-all-copilot-seat-assignments-for-an-organization))

These endpoints are both in beta (as of 21/05/24) and may change in the future.

### Historic Data

This section gathers data from AWS' S3. The CoPilot usage endpoints have a limitation where they only return the last 28 days worth of information. To get around this, the project has an AWS Lambda function which periodically stores data within an S3 bucket. For more information, look at the README.md within the /aws_lambda_script directory ([link](https://github.com/ONS-Innovation/github-copilot-usage-dashboard/blob/master/aws_lambda_scripts/README.md)).

## Getting Started

To setup and use the project, please refer to the READMEs placed within each module.

- [Dashboard Setup](https://github.com/ONS-Innovation/github-copilot-usage-dashboard/blob/master/README.md)
- [Lambda Setup](https://github.com/ONS-Innovation/github-copilot-usage-dashboard/blob/master/aws_lambda_scripts/README.md)