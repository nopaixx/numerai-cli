
### ECS
resource "aws_ecs_cluster" "main" {
  name = local.app_prefix
}

resource "aws_ecs_task_definition" "app" {
  count = length(var.applications)
  family                   = local.app_names[count.index]
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.applications[count.index].cpu
  memory                   = var.applications[count.index].memory
  execution_role_arn       = aws_iam_role.ecsTaskExecutionRole.arn

  container_definitions = jsonencode([
    {
      cpu: var.applications[count.index].cpu,
      image: aws_ecr_repository.app[count.index].repository_url,
      memory: var.applications[count.index].memory,
      name: "app",
      networkMode: "awsvpc",
      portMappings: [
        {
          containerPort: var.app_port,
          hostPort: var.app_port
        }
      ],
      logConfiguration: {
          "logDriver": "awslogs",
          "options": {
              "awslogs-group": aws_cloudwatch_log_group.ecs[count.index].name,
              "awslogs-region": var.aws_region,
              "awslogs-stream-prefix": "ecs"
          }
      }
    }
  ])
}


### Cloudwatch
resource "aws_cloudwatch_log_group" "ecs" {
  count = length(var.applications)
  name              = "/fargate/service/${local.app_names[count.index]}"
  retention_in_days = "14"
}


### ECR
resource "aws_ecr_repository" "app" {
  count = length(var.applications)
  name = local.app_names[count.index]
}


### IAM
resource "aws_iam_role" "ecsTaskExecutionRole" {
  name               = "${local.app_prefix}-ecs"
  assume_role_policy = jsonencode({
    Version: "2012-10-17",
    Statement: [{
      Effect: "Allow",
      Action: "sts:AssumeRole",
      Principal: {
        Service: "ecs-tasks.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ecsTaskExecutionRole_policy" {
  role       = aws_iam_role.ecsTaskExecutionRole.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}
