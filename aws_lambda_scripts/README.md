# AWS Lambda Scripts
This script is used to gather data from the /orgs/{org}/copilot/usage endpoint in the Github API.
The script then appends the collected data to the old data in an S3 bucket.
This creates a record of historical copilot usage data which is used to show trends over time.
The API endpoint above only stores the last 28 days worth of data, meaning this script must run atleast every 28 days to avoid missing data.
This script is run as a containered lambda function in AWS which is executed periodically using EventBridge.

## Setup - Run outside of Docker
1. Navigate into the project's folder and create a virtual environment using `python3 -m venv venv`

2. Activate the virtual environment using `source venv/bin/activate`

3. Install all project dependancies using `pip install -r requirements.txt`

4. Get the copilot-usage-dashboard.pem and copy to the source code root directory (see "Getting a .pem file" below).

5. When running the project locally, you need to edit `main.py`.

When creating an instance of `boto3.Session()`, you must pass which AWS credential profile to use, as found in `~/.aws/credentials`.

When running locally:

```
session = boto3.Session(profile_name="<profile_name>")
s3 = session.client("s3")
```

When running from a container:

```
session = boto3.Session()
s3 = session.client("s3")
```

6. Run the project using `python3 main.py`

## Setup - Running in a container
1. Build a Docker Image

```
    docker build -t copilot-usage-lambda-script .
```

2. Check the image exists

```
    docker images
```

Example Output:

```
REPOSITORY                                                      TAG         IMAGE ID       CREATED          SIZE
copilot-usage-lambda-script                                     latest      0bbe73d9256f   11 seconds ago   224MB
```

3. Run the image locally, passing in AWS credentials to download a .pem file from AWS Secrets Manager to the running container.
These credentials should also allow access to S3 to store the data.

```
docker run \
-e AWS_ACCESS_KEY_ID=<aws_access_key_id> \
-e AWS_SECRET_ACCESS_KEY=<aws_secret_access_key_id> \
-e AWS_DEFAULT_REGION=eu-west-2 \
copilot-usage-lambda-script
```

4. The script will then run and display an output message

```
Added 0 new days to historic_usage_data.json: []
```

5. After execution, the docker container will automatically stop.

## Data Model Diagram (Historic Data)
![Data Model Diagram](./diagrams/aws-lambda-script-data-model.svg)