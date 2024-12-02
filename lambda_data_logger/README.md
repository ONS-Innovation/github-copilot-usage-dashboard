# AWS Lambda Scripts

This script is used to gather data from the /orgs/{org}/copilot/usage endpoint in the Github API.
The script then appends the collected data to the old data in an S3 bucket.
This creates a record of historical copilot usage data which is used to show trends over time.
The script also gets a list of GitHub Teams with CoPilot Usage Data. This is to reduce load times in the frontend.
The API endpoint above only stores the last 28 days worth of data, meaning this script must run atleast every 28 days to avoid missing data.
This script is run as a containered lambda function in AWS which is executed periodically using EventBridge.

## Setup - Running in a container
1. Build a Docker Image

```bash
docker build -t copilot-usage-lambda-script .
```

2. Check the image exists

```bash
docker images
```

Example Output:

```bash
REPOSITORY                                                      TAG         IMAGE ID       CREATED          SIZE
copilot-usage-lambda-script                                     latest      0bbe73d9256f   11 seconds ago   224MB
```

3. Run the image locally mapping local host port (9000) to container port (8080) and passing in AWS credentials to download a .pem file from the AWS Secrets Manager to the running container. These credentials will also be used to upload and download `historic_usage_data.json` to and from S3.

The credentials used in the below command are for a user in AWS that has permissions to retrieve secrets from AWS Secrets Manager and upload and download files from AWS S3.

```bash
docker run --platform linux/amd64 -p 9000:8080 \
-e AWS_ACCESS_KEY_ID=<aws_access_key_id> \
-e AWS_SECRET_ACCESS_KEY=<aws_secret_access_key_id> \
-e AWS_DEFAULT_REGION=eu-west-2 \
-e AWS_SECRET_NAME=<aws_secret_name> \
-e GITHUB_ORG=ONSDigital \
-e GITHUB_APP_CLIENT_ID=<github_app_client_id> \
-e AWS_ACCOUNT_NAME=sdp-sandbox
copilot-usage-lambda-script
```

Once the container is running, a local endpoint is created at `localhost:9000/2015-03-31/functions/function/invocations`.

4. Post to the endpoint to trigger the function

```bash
curl "http://localhost:9000/2015-03-31/functions/function/invocations" -d '{}'
```

5. Once testing is finished, stop the running container

To check the container is running

```bash
docker ps
```

Example output

```bash
CONTAINER ID   IMAGE                         COMMAND                  CREATED          STATUS          PORTS                                       NAMES
3f7d64676b1a   copilot-usage-lambda-script   "/lambda-entrypoint.…"   44 seconds ago   Up 44 seconds   0.0.0.0:9000->8080/tcp, :::9000->8080/tcp   nice_ritchie
```

Stop the container

```bash
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

## Deployment to AWS

The deployment of the service is defined in Infrastructure as Code (IaC) using Terraform.  The service is deployed as a container on an AWS Fargate Service Cluster.

### Deployment Prerequisites

When first deploying the service to AWS the following prerequisites are expected to be in place or added.

#### Underlying AWS Infrastructure

The Terraform in this repository expects that underlying AWS infrastructure is present in AWS to deploy on top of, i.e:

- Route53 DNS Records
- Web Application Firewall and appropriate Rules and Rule Groups
- Virtual Private Cloud with Private and Public Subnets
- Security Groups
- Application Load Balancer
- ECS Service Cluster

That infrastructure is defined in the repository [sdp-infrastructure](https://github.com/ONS-Innovation/sdp-infrastructure)

#### Bootstrap IAM User Groups, Users and an ECSTaskExecutionRole

The following users must be provisioned in AWS IAM:

- ecr-user
  - Used for interaction with the Elastic Container Registry from AWS cli
- terraform-user
  - Used for terraform staging of the resources required to deploy the service

The following groups and permissions must be defined and applied to the above users:

- ecr-user-group
  - EC2 Container Registry Access
- terraform-user-group
  - Dynamo DB Access
  - EC2 Access
  - ECS Access
  - ECS Task Execution Role Policy
  - Route53 Access
  - S3 Access
  - Cloudwatch Logs All Access (Custom Policy)
  - IAM Access
  - Secrets Manager Access

**The Lambda Script Terraform requires some additional permissions to those above:**

- AmazonEC2ContainerRegistryFullAccess
- AmazonEventBridgeFullAccess
- AWSLambda_FullAccess

Further to the above an IAM Role must be defined to allow ECS tasks to be executed:

- ecsTaskExecutionRole
  - See the [AWS guide to create the task execution role policy](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_execution_IAM_role.html)

#### Bootstrap for Terraform

To store the state and implement a state locking mechanism for the service resources a Terraform backend is deployed in AWS (an S3 object and DynamoDbTable).

#### Running the Terraform

There are associated README files in each of the Terraform modules in this repository.  

- terraform/dashboard/main.tf
  - This provisions the resources required to launch the Copilot Usage Dashboard iteself.
- terraform/data_logger/main.tf
  - This provisions the resources required to launch the Copilot Dashboard's data collection Lambda script (data logger).

Depending upon which environment you are deploying to you will want to run your terraform by pointing at an appropriate environment tfvars file.  

Example service tfvars file:
[/env/sandbox/example_tfvars.txt](../terraform/dashboard/env/sandbox/example_tfvars.txt)

### Updating the running service using Terraform (data_logger)

If the application has been modified then the following can be performed to update the running service:

- Build a new version of the container image and upload to ECR as per the instructions earlier in this guide.
- Change directory to the **terraform/data_logger**

  ```bash
  cd terraform/data_logger
  ```

- In the appropriate environment variable file env/sandbox/sandbox.tfvars, env/dev/dev.tfvars or env/prod/prod.tfvars
  - Fill out the appropriate variables

- Initialise terraform for the appropriate environment config file _backend-dev.tfbackend_ or _backend-prod.tfbackend_ run:

  ```bash
  terraform init -backend-config=env/dev/backend-dev.tfbackend -reconfigure
  ```

  The reconfigure options ensures that the backend state is reconfigured to point to the appropriate S3 bucket.

  **_Please Note:_** This step requires an **AWS_ACCESS_KEY_ID** and **AWS_SECRET_ACCESS_KEY** to be loaded into the environment if not already in place.
  This can be done using:

  ```bash
  export AWS_ACCESS_KEY_ID="<aws_access_key_id>"
  export AWS_SECRET_ACCESS_KEY="<aws_secret_access_key>"
  ```

- Refresh the local state to ensure it is in sync with the backend

  ```bash
  terraform refresh -var-file=env/dev/dev.tfvars
  ```

- Plan the changes, ensuring you use the correct environment config (depending upon which env you are configuring):

  E.g. for the dev environment run

  ```bash
  terraform plan -var-file=env/dev/dev.tfvars
  ```

- Apply the changes, ensuring you use the correct environment config (depending upon which env you are configuring):

  E.g. for the dev environment run

  ```bash
  terraform apply -var-file=env/dev/dev.tfvars
  ```

- When the terraform has applied successfully the Lambda and EventBridge Schedule will be created.

### Destroy the Main Service Resources

Delete the service resources by running the following ensuring your reference the correct environment files for the backend-config and var files:

  ```bash
  cd terraform/data_logger

  terraform init -backend-config=env/dev/backend-dev.tfbackend -reconfigure

  terraform refresh -var-file=env/dev/dev.tfvars

  terraform destroy -var-file=env/dev/dev.tfvars
  ```