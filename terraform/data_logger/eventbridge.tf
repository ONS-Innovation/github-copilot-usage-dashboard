module "eventbridge" {
  source = "terraform-aws-modules/eventbridge/aws"

  create_bus = false

  rules = {
    crons = {
      description         = "Trigger for Lambda Function"
      schedule_expression = var.schedule
    }
  }

  targets = {
    crons = [
      {
        name  = "lambda-function-cron"
        arn   = aws_lambda_function.lambda_function.arn
        input = jsonencode({})
      }
    ]
  }
}

resource "aws_lambda_permission" "allow_eventbridge_to_invoke_lambda" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.lambda_function.arn
  principal     = "events.amazonaws.com"
  source_arn    = module.eventbridge.eventbridge_rules["crons"]["arn"]
}