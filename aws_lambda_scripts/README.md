# AWS Lambda Scripts
This script is used to gather data from the /orgs/{org}/copilot/usage endpoint in the Github API.
The script then appends the collected data to the old data in an S3 bucket.
This creates a record of historical copilot usage data which is used to show trends over time.
The API endpoint above only stores the last 28 days worth of data, meaning this script must run atleast every 28 days to avoid missing data.
This script is run as a containered lambda function in AWS which is executed periodically using EventBridge.

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

3. Run the image locally mapping local host port (9000) to container port (8080) and passing in AWS credentials to download a .pem file from the AWS Secrets Manager to the running container. These credentials will also be used to upload and download `historic_usage_data.json` to and from S3.

The credentials used in the below command are for a user in AWS that has permissions to retrieve secrets from AWS Secrets Manager and upload and download files from AWS S3.

```
docker run --platform linux/amd64 -p 9000:8080 \
-e AWS_ACCESS_KEY_ID=<aws_access_key_id> \
-e AWS_SECRET_ACCESS_KEY=<aws_secret_access_key_id> \
-e AWS_DEFAULT_REGION=eu-west-2 \
copilot-usage-lambda-script
```

Once the container is running, a local endpoint is created at `localhost:9000/2015-03-31/functions/function/invocations`.

4. Post to the endpoint to trigger the function

```
curl "http://localhost:9000/2015-03-31/functions/function/invocations" -d '{}'
```

5. Once testing is finished, stop the running container

To check the container is running

```
docker ps
```

Example output

```
CONTAINER ID   IMAGE                         COMMAND                  CREATED          STATUS          PORTS                                       NAMES
3f7d64676b1a   copilot-usage-lambda-script   "/lambda-entrypoint.…"   44 seconds ago   Up 44 seconds   0.0.0.0:9000->8080/tcp, :::9000->8080/tcp   nice_ritchie
```

Stop the container

```
docker stop 3f7d64676b1a
```

## Storing the container on AWS Elastic Container Registry (ECR)

When you make changes to the Lambda Script, a new container image must be pushed to ECR.

These instructions assume:

1. You have a repository set up in your AWS account named copilot-usage-lambda-script.
2. You have created an AWS IAM user with permissions to read/write to ECR (e.g AmazonEC2ContainerRegistryFullAccess policy) and that you have created the necessary access keys for this user.  The credentials for this user are stored in ~/.aws/credentials and can be used by accessing --profile <aws-credentials-profile\>, if these are the only credentials in your file then the profile name is _default_

You can find the AWS repo push commands under your repository in ECR by selecting the "View Push Commands" button.  This will display a guide to the following (replace <aws-credentials-profile\>, <aws-account-id\> and <version\> accordingly):

1. Get an authentication token and authenticate your docker client for pushing images to ECR:

    ```bash
    aws ecr --profile <aws-credentials-profile> get-login-password --region eu-west-2 | docker login --username AWS --password-stdin <aws-account-id>.dkr.ecr.eu-west-2.amazonaws.com
    ```

2. Tag your latest built docker image for ECR (assumes you have run _docker build -t sdp-repo-archive ._ locally first)

    ```bash
    docker tag copilot-usage-lambda-script:latest <aws-account-id>.dkr.ecr.eu-west-2.amazonaws.com/copilot-usage-lambda-script:<version>
    ```

    **Note:** To find the <version\> to build look at the latest tagged version in ECR and increment appropriately

3. Push the version up to ECR

    ```bash
    docker push <aws-account-id>.dkr.ecr.eu-west-2.amazonaws.com/copilot-usage-lambda-script:<version>
    ```

## Data Model Diagram (Historic Data)
![Data Model Diagram](./diagrams/aws-lambda-script-data-model.svg)