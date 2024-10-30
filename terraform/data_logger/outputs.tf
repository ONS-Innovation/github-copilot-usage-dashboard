output "lambda_name" {
  value = aws_lambda_function.lambda_function.function_name
}

output "lambda_image" {
  value = aws_lambda_function.lambda_function.image_uri
}

output "lambda_role" {
  value = aws_lambda_function.lambda_function.role
}

output "repo_name" {
  value = local.lambda_repo
}

output "rule_arn" {
  value = module.eventbridge.eventbridge_rules["crons"]["arn"]
}