# Service Terraform

This terraform must be run to provision the ECS Fargate service and task definition used to run the Copilot Usage Dashboard.

## Prerequisites

The service terraform is bootstrapped with a separate terraform state key so that terraform state files are separated.

## Apply the Terraform

Depending upon which environment you are deploying to you will want to run your terraform by pointing at an appropriate environment tfvars file.  

Example service tfvars file:
[service/env/sandbox/example_tfvars.txt](https://github.com/ONS-Innovation/code-github-copilot-usage-audit/terraform/service/env/sandbox/example_tfvars.txt)

### Update Existing Service

If you are just upgrading the application logic then only the service terraform needs to be run.

When upgrading:

- Ensure the container_ver variable is set to the appropriate version in the relevant env tfvar file
- Ensure the force_deployment flag is set to true in the relevant env tfvar file
- Ensure the terraform is configured to point at the appropriate backend
- Ensure the terraform plan and apply select the appropriate environment variable file

```bash
terraform init -backend-config=env/dev/backend-dev.tfbackend -reconfigure

terraform validate

terraform plan -var-file=env/dev/dev.tfvars

terraform apply -var-file=env/dev/dev.tfvars
```

### Provision Service from Scratch

Ensure that IAM roles and a terraform backend using S3 and dynamoDB are provisioned.

Apply the terraform for this service

```bash
cd terraform/service 

terraform init -backend-config=env/dev/backend-dev.tfbackend -reconfigure

terraform validate

terraform plan -var-file=env/dev/dev.tfvars

terraform apply -var-file=env/dev/dev.tfvars
```

## Resources

The IaC creates the following resources:

- Target Group
- Application Load Balancer service rule to authenticate via Cognito
- Application Load Balancer service rule to bypass Cognito authentication for certain URLs
- Route 53 Record to map service URL through to Application Load Balancer
- Security Group to apply to Service restricting traffic on designated ports
- ECS Task Definition
- ECS Service  
