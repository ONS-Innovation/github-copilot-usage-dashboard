# AWS Lambda Scripts
This script is used to gather data from the /orgs/{org}/copilot/usage endpoint in the Github API.
The script then appends the collected data to the old data in an S3 bucket.
This creates a record of historical copilot usage data which is used to show trends over time.
The API endpoint above only stores the last 28 days worth of data, meaning this script must run atleast every 28 days to avoid missing data.
This script is run as a containered lambda function in AWS which is executed periodically using EventBridge.

## Setup


## Data Model Diagram (Historic Data)
![Data Model Diagram](./diagrams/aws-lambda-script-data-model.svg)