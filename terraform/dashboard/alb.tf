# Update the Application Load Balancer to forward appropriate requests
# to the backend service running in ECS Fargate.
# Create target group, used by ALB to forward requests to ECS service
resource "aws_lb_target_group" "service_fargate_tg" {
  name        = "${var.service_subdomain}-fargate-tg"
  port        = 80
  protocol    = "HTTP"
  target_type = "ip"
  vpc_id      = data.terraform_remote_state.ecs_infrastructure.outputs.vpc_id
}

# Use the module to get highest current priority
module "alb_listener_priority" {
  source                = "git::https://github.com/ONS-Innovation/keh-alb-listener-tf-module.git?ref=v1.0.0"
  aws_access_key_id     = var.aws_access_key_id
  aws_secret_access_key = var.aws_secret_access_key
  region                = var.region
  listener_arn          = data.terraform_remote_state.ecs_infrastructure.outputs.application_lb_https_listener_arn
}

# Create a listener rule to forward requests to the target group
resource "aws_lb_listener_rule" "service_listener_rule" {
  listener_arn = data.terraform_remote_state.ecs_infrastructure.outputs.application_lb_https_listener_arn
  priority     = module.alb_listener_priority.highest_priority + 1

  condition {
    host_header {
      values = ["${local.service_url}"]
    }
  }

  dynamic "action" {
    for_each = var.authenticate_users ? [1] : []

    content {
      type = "authenticate-cognito"

      authenticate_cognito {
        user_pool_arn       = data.terraform_remote_state.ecs_auth.outputs.service_user_pool_arn
        user_pool_client_id = data.terraform_remote_state.ecs_auth.outputs.service_user_pool_client_id
        user_pool_domain    = data.terraform_remote_state.ecs_auth.outputs.service_user_pool_domain
      }
    }
  }

  action {
    target_group_arn = aws_lb_target_group.service_fargate_tg.arn
    type             = "forward"
  }
}