variable "aws_account_id" {
  description = "AWS Account ID"
  type        = string
}

variable "aws_access_key_id" {
  description = "AWS Access Key ID"
  type        = string
}

variable "aws_secret_access_key" {
  description = "AWS Secret Access Key"
  type        = string
}

variable "aws_secret_name" {
  description = "The path to the AWS Secret Manager resource which contains the Github App .pem file"
  type        = string
}

variable "container_image" {
  description = "Container image"
  type        = string
  default     = "example-service"
}

variable "container_ver" {
  description = "Container tag"
  type        = string
  default     = "v0.0.1"

}

variable "container_port" {
  description = "Container port"
  type        = number
  default     = 5000
}

variable "from_port" {
  description = "From port"
  type        = number
  default     = 5000
}

variable "service_subdomain" {
  description = "Service subdomain"
  type        = string
  default     = "example-service"
}

variable "domain" {
  description = "Domain"
  type        = string
  default     = "sdp-sandbox"
}

variable "domain_extension" {
  description = "Domain extension"
  type        = string
  default     = "aws.onsdigital.uk"
}

variable "service_cpu" {
  description = "Service CPU"
  type        = string
  default     = "1024"
}

variable "service_memory" {
  description = "Service memory"
  type        = string
  default     = "3072"
}

variable "task_count" {
  description = "Number of instances of the service to run"
  type        = number
  default     = 1
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "eu-west-2"
}

variable "log_retention_days" {
  description = "Log retention days"
  type        = number
  default     = 90
}

variable "github_org" {
  description = "Github Organisation"
  type        = string
  default     = "ONS-Innovation"
}

variable "github_app_client_id" {
  description = "Github App Client ID"
  type        = string
}

variable "project_tag" {
  description = "Project"
  type        = string
  default     = "SDP"
}

variable "team_owner_tag" {
  description = "Team Owner"
  type        = string
  default     = "Knowledge Exchange Hub"
}

variable "business_owner_tag" {
  description = "Business Owner"
  type        = string
  default     = "DST"
}

variable "authenticate_users" {
  description = "Authenticate users"
  type        = bool
  default     = false
}


variable "force_deployment" {
  description = "Force new task definition deployment"
  type        = string
  default     = "false"
}

locals {
  url         = "${var.domain}.${var.domain_extension}"
  service_url = "${var.service_subdomain}.${local.url}"
}