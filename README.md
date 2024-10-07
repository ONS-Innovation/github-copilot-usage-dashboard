# GitHub Copilot Usage Dashboard

A Streamlit dashboard to display information from the Github Copilot Usage API endpoints.

## Disclaimer
### Early Stage & Accessibility Disclaimer

Please note that the code available in this repository for creating a Dashboard to track GitHub Copilot usage within your organisation is in its **early stages of development**. It may **not** fully comply with all Civil Service / ONS best practices for software development. Currently, it is being used by a **limited number of individuals** within ONS. Additionally, due to the limited number of users, this project has **not** been tested for WACG 2.1 compliance nor accessibility. Please consider this when using the project.

### Purpose of Early Sharing

We are sharing this piece of code at this stage to enable other Civil Service entities to utilise it as soon as possible.

### Collaboration and Contribution

Feel free to **fork this repository** and use it as you see fit. If you wish to contribute to this work, please make a pull request, and we will consider adding you as an external collaborator.

## Prerequisites

This project uses poetry for package management.

[Instructions to install Poetry](https://python-poetry.org/docs/)

## Documentation

This project uses MkDocs for documentation.

[Getting started with MkDocs](https://www.mkdocs.org/getting-started/)

## Setup - Run outside of Docker

Prior to running outside of Docker ensure you have the necessary environment variables setup locally where you are running the application. E.g in linux or OSX you can run the following, providing appropriate values for the variables:

```bash
export AWS_ACCESS_KEY_ID=<aws_access_key_id> 
export AWS_SECRET_ACCESS_KEY=<aws_secret_access_key_id> 
export AWS_DEFAULT_REGION=eu-west-2 
export AWS_SECRET_NAME=<aws_secret_name> 
export GITHUB_ORG=ONSDigital 
export GITHUB_APP_CLIENT_ID=<github_app_client_id>
export AWS_ACCOUNT_NAME=sdp-sandbox
```

1. Navigate into the project's folder and create a virtual environment using `python3 -m venv venv`
2. Activate the virtual environment using `source venv/bin/activate`
3. Install all project dependancies using `make install`
4. When running the project locally, you need to edit `app.py`.

    When creating an instance of `boto3.Session()`, you must pass which AWS credential profile to use, as found in `~/.aws/credentials`.

    When running locally:

    ```python
    session = boto3.Session(profile_name="<profile_name>")
    ```

    When running from a container:

    ```python
    session = boto3.Session()
    ```

5. Run the project using `streamlit run src/app.py`

## Setup Team Usage Page

For testing purposes, create a 'New OAuth App' by going to this [page](https://github.com/settings/developers). You can name the app anything (can't start with git or github) e.g. copilot-usage-auth-app. Note down the Client ID and Client secret.

- Set the application name to anything.
- Set the homepage URL to `http://localhost:8502`.
- Set the authorization callback URL to `http://localhost:8502/team_usage`.

Install the code as usual, by creating the virtual environment, `make install`. The additional dependencies that have been added are `github-api-toolkit` and `requests`.

Take your generated client ID and secret and import them using export.

```bash
export AWS_ACCESS_KEY_ID=<aws_access_key_id> 
export AWS_SECRET_ACCESS_KEY=<aws_secret_access_key_id> 
export AWS_DEFAULT_REGION=eu-west-2 
export AWS_SECRET_NAME=<aws_secret_name> 
export GITHUB_ORG=ONSDigital 
export GITHUB_APP_CLIENT_ID=<github_app_client_id>
export AWS_ACCOUNT_NAME=sdp-sandbox
```

```bash
export CLIENT_ID=<client_id>
export CLIENT_SECRET=<client_secret>
```

Make sure no other apps are running on `localhost:8502`. Once setup, use `make run-local`. This runs the the streamlit app on port **8502**, as *8501* is the default port.

Once the app is running, head to `localhost:8502/team_usage` or by clicking the `Team Usage` in the sidebar. Click the `Login with GitHub` button. This redirects the user to the GitHub OAuth page. Click the green `Authorize` button, which redirects you back to the main application and logs you in.

If you are part of the `keh-dev` team then you can either select a team that you are in from the select box or you can enter another team name. As of 30-09-2024, there are only these teams with team copilot data: `all`, `Blaise5`, `CSS`, `keh-dev`, `Ops`.

If you are not part of the `keh-dev` team then you can select a team that you are in from the select box.

**IMPORTANT**
The team must have a **minimum of 5 users with active copilot licenses**. 
The team must be in the ONSDigital org.
The authorized user (your account) must be in that team.

## Setup - Running in a container

1. Build a Docker Image

    ```bash
    docker build -t copilot-usage-dashboard .
    ```

2. Check the image exists

    ```bash
    docker images
    ```

    Example Output:

    ```bash
    REPOSITORY                                                      TAG         IMAGE ID       CREATED          SIZE
    copilot-usage-dashboard                                         latest      afa0494f35a5   7 minutes ago    1.02GB
    ```

3. Run the image locally mapping local port 5801 to container port 5801 and passing in AWS credentials to download a .pem file from AWS Secrets Manager to the running container.
These credentials should also allow access to S3 for historic reporting.

    ```bash
    docker run -p 8501:8501 \
    -e AWS_ACCESS_KEY_ID=<aws_access_key_id> \
    -e AWS_SECRET_ACCESS_KEY=<aws_secret_access_key_id> \
    -e AWS_DEFAULT_REGION=eu-west-2 \
    -e AWS_SECRET_NAME=<aws_secret_name> \
    -e GITHUB_ORG=ONSDigital \
    -e GITHUB_APP_CLIENT_ID=<github_app_client_id> \
    -e AWS_ACCOUNT_NAME=sdp-sandbox
    copilot-usage-dashboard
    ```

4. Check the container is running

    ```bash
    docker ps
    ```

    Example Output:

    ```bash
    CONTAINER ID   IMAGE                     COMMAND                  CREATED         STATUS         PORTS                                       NAMES
    ae4aaf1daee6   copilot-usage-dashboard   "/app/start_dashboar…"   7 seconds ago   Up 6 seconds   0.0.0.0:8501->8501/tcp, :::8501->8501/tcp   quirky_faraday
    ```

5. To view the running in a browser app navigate to

    ```bash
    You can now view your Streamlit app in your browser.

    URL: http://0.0.0.0:8501
    ```

6. To stop the container, use the container ID

    ```bash
    docker stop ae4aaf1daee6
    ```

## Storing the container on AWS Elastic Container Registry (ECR)

When you make changes to the application a new container image must be pushed to ECR.

These instructions assume:

1. You have a repository set up in your AWS account named copilot-usage-dashboard.
2. You have created an AWS IAM user with permissions to read/write to ECR (e.g AmazonEC2ContainerRegistryFullAccess policy) and that you have created the necessary access keys for this user.  The credentials for this user are stored in ~/.aws/credentials and can be used by accessing --profile <aws-credentials-profile\>, if these are the only credentials in your file then the profile name is _default_

You can find the AWS repo push commands under your repository in ECR by selecting the "View Push Commands" button.  This will display a guide to the following (replace <aws-credentials-profile\>, <aws-account-id\> and <version\> accordingly):

1. Get an authentication token and authenticate your docker client for pushing images to ECR:

    ```bash
    aws ecr --profile <aws-credentials-profile> get-login-password --region eu-west-2 | docker login --username AWS --password-stdin <aws-account-id>.dkr.ecr.eu-west-2.amazonaws.com
    ```

2. Tag your latest built docker image for ECR (assumes you have run _docker build -t sdp-repo-archive ._ locally first)

    ```bash
    docker tag copilot-usage-dashboard:latest <aws-account-id>.dkr.ecr.eu-west-2.amazonaws.com/copilot-usage-dashboard:<version>
    ```

    **Note:** To find the <version\> to build look at the latest tagged version in ECR and increment appropriately

3. Push the version up to ECR

    ```bash
    docker push <aws-account-id>.dkr.ecr.eu-west-2.amazonaws.com/copilot-usage-dashboard:<version>
    ```

## Data

When running the dashboard, you can toggle between using Live and Example Data.

To use real data from the Github API, the project must be supplied with a copilot-usage-dashboard.pem file in AWS Secret Manager (as mentioned [here](./readme.md/#bootstrap-for-secrets-manager)). 

This project also supports historic reporting outside of the 28 days which the API supplies. For more information on setup, please see this [README.md](../aws_lambda_scripts/README.md).

## Github App Permissions

A .pem file is used to allow the project to make authorised Github API requests through the means of Github App authentication.
The project uses authentication as a Github App installation ([documentation](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/authenticating-as-a-github-app-installation)).

In order to get a .pem file, a Github App must be created an installed into the organisation of which the app will be managing.
This app should have **Read and Write Administration** organisation permission and **Read-only GitHub Copilot Business** organisation permission.

This file should be uploaded to AWS Secret Manager as below.

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
- ecs-app-user
  - Used for terraform staging of the resources required to deploy the service

The following groups and permissions must be defined and applied to the above users:

- ecr-user-group
  - EC2 Container Registry Access
- ecs-application-user-group
  - Dynamo DB Access
  - EC2 Access
  - ECS Access
  - ECS Task Execution Role Policy
  - Route53 Access
  - S3 Access
  - Cloudwatch Logs All Access (Custom Policy)
  - IAM Access
  - Secrets Manager Access

Further to the above an IAM Role must be defined to allow ECS tasks to be executed:

- ecsTaskExecutionRole
  - See the [AWS guide to create the task execution role policy](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_execution_IAM_role.html)

#### Bootstrap for Terraform

To store the state and implement a state locking mechanism for the service resources a Terraform backend is deployed in AWS (an S3 object and DynamoDbTable).

#### Bootstrap for Secrets Manager

The service requires access to an associated Github App secret, this secret is created when the Github App is installed in the appropriate Github Organisation.  The contents of the generated pem file is stored in the AWS Secret Manager and retrieved by this service to interact with Github securely.

AWS Secret Manager must be set up with a secret:

- /sdp/tools/copilot-uasge/copilot-usage-dashboard.pem
  - A plaintext secret, containing the contents of the .pem file created when a Github App was installed.

#### Running the Terraform

There are associated README files in each of the Terraform modules in this repository.  

- terraform/service/main.tf
  - This provisions the resources required to launch the service.

Depending upon which environment you are deploying to you will want to run your terraform by pointing at an appropriate environment tfvars file.  

Example service tfvars file:
[service/env/sandbox/example_tfvars.txt](https://github.com/ONS-Innovation/code-github-copilot-usage-audit/terraform/service/env/sandbox/example_tfvars.txt)

### Updating the running service using Terraform

If the application has been modified then the following can be performed to update the running service:

- Build a new version of the container image and upload to ECR as per the instructions earlier in this guide.
- Change directory to the **service terraform**

  ```bash
  cd terraform/service
  ```

- In the appropriate environment variable file env/sandbox/sandbox.tfvars, env/dev/dev.tfvars or env/prod/prod.tfvars
  - Change the _container_ver_ variable to the new version of your container.
  - Change the _force_deployment_ variable to _true_.

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

- When the terraform has applied successfully the running task will have been replaced by a task running the container version you specified in the tfvars file

### Destroy the Main Service Resources

Delete the service resources by running the following ensuring your reference the correct environment files for the backend-config and var files:

  ```bash
  cd terraform/service

  terraform init -backend-config=env/dev/backend-dev.tfbackend -reconfigure

  terraform refresh -var-file=env/dev/dev.tfvars

  terraform destroy -var-file=env/dev/dev.tfvars
  ```

  ## Linting and Formatting
To view all commands
```bash
make all
```

Linting tools must first be installed before they can be used
```bash
make install-dev
```

To clean residue files
```bash
make clean
```

To format your code
```bash
make format
```

To run all linting tools
```bash
make lint
```

To run a specific linter (black, ruff, pylint)
```bash
make black
make ruff
make pylint
```

To run mypy (static type checking)
```bash
make mypy
```


To run the application locally
```bash
make run-local
```
