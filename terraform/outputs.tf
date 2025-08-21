output "lambda_name" {
  description = "Name of the Lambda function"
  value       = aws_lambda_function.lambda_function.function_name
}

output "lambda_image" {
  description = "URI of the Lambda function container image in ECR"
  value       = aws_lambda_function.lambda_function.image_uri
}

output "lambda_role" {
  description = "ARN of the IAM role attached to the Lambda function"
  value       = aws_lambda_function.lambda_function.role
}

output "repo_name" {
  description = "Name of the ECR repository"
  value       = local.lambda_repo
}

output "rule_arn" {
  description = "ARN of the EventBridge rule"
  value       = module.eventbridge.eventbridge_rules["${var.lambda_name}-crons"]["arn"]
}