# GitHub Copilot Usage Dashboard

## Overview

This project contains a dashboard which displays ONSDigital's GitHub CoPilot usage metrics via the GitHub RESTful API. The dashboard is written in Python and uses [Streamlit](https://streamlit.io/) to produce a quick, easy and responsive UI. This project also makes use of a library called [Plotly](https://plotly.com/python/) to produce high quality and interactive graphs.

## High Level Data Overview
### Live Data

The data used within this section of the tool is pulled directly from the GitHub API at runtime. This data is dependant on a GitHub App being setup within the target organisation, with the correct permissions (as outlined in the [README](./readme.md/#github-app-permissions)).

### Historic Data

This section gathers data from AWS' S3. The CoPilot usage endpoints have a limitation where they only return the last 28 days worth of information. To get around this, the project has an AWS Lambda function which periodically stores data within an S3 bucket. For more information, look at the README.md within aws_lambda_script.

## Techstack Overview
### Streamlit

[Streamlit](https://streamlit.io/) is a powerful web framework which promotes creating apps quickly and without the need of any frontend writing. This makes Streamlit well suited to the project due to the speed of development and heavy data focus. Streamlit also promotes interactivity within its apps which is crucial when making a dashboard as you want users to be able to play with the data to get the most from it. This project has been used as a proof of concept for Streamlit, testing its capabilities and potential for future projects. A small drawback is Streamlit's potential lack of accessibility. This project hasn't been accessibility tested but, due to its limited target audience, is still fit for purpose. Another limitation of the tool is its ability to be customised to look and feel like an ONS product. Streamlit offers customisation within its colour scheme and allows logos to be added, however it will still look like a Streamlit application.

### Plotly

[Plotly](https://plotly.com/python/) is a graphing library used within the project. Plotly was chosen because of its high interactivity, ability to export and general ease of use alongside Streamlit. Other libraries, such as Matplotlib, were trialed alongside Plotly during early development. It was found that Plotly just generally suited Streamlit's feel and focus on interactivity, which is why it was chosen. Another advantage of Plotly was its incorporation with [Dash](https://dash.plotly.com/), a dashboarding tool built on top of the Flask framework. This means that if Dash was to be used in the future (perhaps to onboard a dashboard onto the ONS Design System), we'd already have some knowledge on how to use it.