# GitHub Copilot Usage Dashboard

A Streamlit dashboard to display information from the Github Copilot Usage API endpoints.

---

## Important Notice

This repository is currently using depreciated endpoints to collect CoPilot Usage information and will not be able to show information past the 1st of February 2025.

We are working on refactoring the dashboard and its lambda to make use of the new endpoints and its data structure.

| Documentation | Link |
| ------------- | ---- |
| Old Endpoint  | https://docs.github.com/en/rest/copilot/copilot-usage?apiVersion=2022-11-28 |
| New Endpoint  | https://docs.github.com/en/rest/copilot/copilot-metrics?apiVersion=2022-11-28 |

---

## Interim Solution

While we work on refactoring the CoPilot Dashboard, this repository will contain a temporary solution.

This solution will display high-level information from the new API endpoints.

The old dashboard pages (Organisation Usage & Team Usage) have been toggled to use example data in order to still see them.

The data on these pages is completely synthetic.

---

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

This project uses MkDocs for documentation which gets deployed to GitHub Pages at a repository level.

For more information about MkDocs, see the below documentation.

[Getting Started with MkDocs](https://www.mkdocs.org/getting-started/)

There is a guide to getting started on this repository's GitHub Pages site.

## Setup - Run outside of Docker

Prior to running outside of Docker ensure you have the necessary environment variables setup locally where you are running the application. E.g in linux or OSX you can run the following, providing appropriate values for the variables:

```bash
export AWS_ACCESS_KEY_ID=<aws_access_key_id> 
export AWS_SECRET_ACCESS_KEY=<aws_secret_access_key_id> 
export AWS_DEFAULT_REGION=eu-west-2 
export AWS_SECRET_NAME=<aws_secret_name> 
export GITHUB_ORG=ONSDigital 
export GITHUB_APP_CLIENT_ID=<github_app_client_id>
export GITHUB_APP_CLIENT_SECRET=<github_app_client_secret>
export AWS_ACCOUNT_NAME=sdp-sandbox
export APP_URL=http://localhost:8501
```

**Please Note:**

- APP_URL should point to the url which the app is running at. For example, if running locally you'd use localhost:8501 and on AWS the appropriate domain url.
- The GITHUB_APP_CLIENT_ID and GITHUB_APP_CLIENT_SECRET can be found from the GitHub App in developer settings.

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
    -e GITHUB_APP_CLIENT_SECRET=<github_app_client_secret> \
    -e AWS_ACCOUNT_NAME=sdp-sandbox \
    -e APP_URL=http://localhost:8501
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

### Scripted Push to ECR

This script assumes you have a ~/.aws/credentials file set up with profiles of the credentials for pushing to ECR and that a suitably named repository (environmentname-toolname) is already created in the ECR.  In the credential file you should use the profile that matches the IAM user associated with permissions to push to the ECR.

Setup the environment for the correct credentials. Ensure the script is executable:

```bash
chmod a+x set_aws_env.sh
```

Run the script:

```bash
./set_aws_env.sh <aws-profile e.g ons_sdp_dev_ecr> <environment  e.g sdp-dev> 
```

Verify the output is as expected:

```bash
Environment variables are set as:
export AWS_ACCESS_KEY_ID=MYACCESSKEY
export AWS_SECRET_ACCESS_KEY=MYSECRETACCESSKEY
export AWS_DEFAULT_REGION=eu-west-2
export APP_NAME=sdp-dev-copilot-usage
```

Ensure the script to build and push the image is executable:

```bash
chmod a+x publish_container.sh
```

Check the version of the image you want to build (verify the next available release by looking in ECR)

Run the script, which will build an image locally, connect to ECR, push the image and then check the image is uploaded correctly.

```bash
./publish_container.sh <AWS Profile - e.g ons_sdp_dev_ecr> <AWS_ACCOUNT_NUMBER> <AWS Env - e.g sdp-dev> <image version - e.g v0.0.1>
```

### Manual Push to ECR

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

## Team Usage Page

This page shows CoPilot Usage at a team level.

The user will be prompted to login to GitHub on the page.

Logged in users will only be able to see teams that they are a member of.

If the logged in user is apart of an admin team, they can search for and view any team's metrics. See [Updating Admin Teams](#updating-admin-teams) for more information.

**Please Note:**

- The team must have a **minimum of 5 users with active copilot licenses** to have any data.
- The team must be in the organisation the tool is running in.

### Updating Admin Teams

Currently, there are 2 admin teams `keh-dev` and `sdp-dev`.

These teams are defined in `admin_teams.json` in the `copilot-usage-dashboard` bucket.

To add another admin team, simply add the team name to `admin_teams.json`.


`admin_teams.json` is in the following format and must be created manually on a fresh deployment:

```json
["team-A", "team-B"]
```

### Permissions

A .pem file is used to allow the project to make authorised Github API requests through the means of Github App authentication.
The project uses authentication as a Github App installation ([documentation](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/authenticating-as-a-github-app-installation)).

In order to get a .pem file, a Github App must be created an installed into the organisation of which the app will be managing.
This app should have **Read and Write Administration** organisation permission and **Read-only GitHub Copilot Business** organisation permission.

This file should be uploaded to AWS Secret Manager as below.

### Callback URLs

It is vital that a callback URL is added to allow a login through GitHub when using the `/team_usage` page.

To do this, add `<app_url>/team_usage` as a callback url within your GitHub App's settings.

If you receive an error about an **invalid callback uri**, this callback url either doesn't exist or is incorrect.

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

- /sdp/tools/copilot-usage/copilot-usage-dashboard.pem
  - A plaintext secret, containing the contents of the .pem file created when a Github App was installed.

#### Running the Terraform

There are associated README files in each of the Terraform modules in this repository.  

- terraform/service/main.tf
  - This provisions the resources required to launch the service.

Depending upon which environment you are deploying to you will want to run your terraform by pointing at an appropriate environment tfvars file.  

Example service tfvars file:
[dashboard/env/sandbox/example_tfvars.txt](./terraform/dashboard/env/sandbox/example_tfvars.txt)

### Updating the running service using Terraform

If the application has been modified then the following can be performed to update the running service:

- Build a new version of the container image and upload to ECR as per the instructions earlier in this guide.
- Change directory to the **dashboard terraform**

  ```bash
  cd terraform/dashboard
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
  cd terraform/dashboard

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
