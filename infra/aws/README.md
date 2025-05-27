## Before You Deploy: Key Notes
1. Build Docker Image for ECR Compatibility. Use command: 'docker build --platform linux/amd64 -t database-webapp .' in the cli while in the correct directory 
during building image for ECR repository, from which Task will pull the image for the app. It's crucial for the compatibility
with ECS Fargate, which runs on linux/amd64 architecture. Do this to avoid 'CannotPullContainerError'.
2. Enable CloudWatch Logs for ECS Tasks. Attach CloudWatchLogsFullAccess Policy to ecsTaskExecutionRole in order to enable access to Cloud Watch
for the ECS tasks for monitoring and debugging.
3. Health Check Configuration. The healthcheck of the task (Backend Python API) is highly optional since the Application Load Balancers (attached 
to the ECS service) target group has the healthcheck configured at the /health route anyway.

Manual documentation for the Amazon RDS Instance setup (which serves as the Database for the application deployed on the ECS cluster) :
- Database Engine: PostgreSQL,
- Database Name: chemical_db,
- Endpoint (host name for the database connection string in the app) : db.c9o6ae2y8y23.eu-central-1.rds.amazonaws.com,
- Port (port on which the database listens): 5432
- Master Username and Password: Managed by AWS Secrets Manager through arn specifically bound to each
- VPC: vpc-01a5c2ecad02a83bc (Must match the ECS's associated service VPC to ensure feasible communication),
- Security Group: sg-088b146df3e2dc1eb (Instances (resources) from within this security group need to have access to each other),
- Backup Retention: 7 days,

Manual Documentation for the ECS Cluster setup (which serves as the hosting environment for the application) :
- Cluster Name: Database_web_app_cluster
- Cluster Type: ECS Cluster running on Fargate
- Networking Mode: awsvpc

Manual Documentation for the ECS Service setup:
- Service Name: RunDatabase
- Task Definition: Database-Python-web-app
- Revision: latest 
- Desired Count: 1
- Deployment Configuration: Rolling Update (default behavior)
    Networking configuration:
- VPC: vpc-01a5c2ecad02a83bc
- Subnets: All available subnets in the VPC (default behavior).
- Security Groups:
 1. SG 1: sg-088b146df3e2dc1eb (default security group) — Used for internal communication between instances within the security group.
 2. SG 2: sg-0f14c1bb83e0a3277 — Allowing incoming HTTP/ HTTPS traffic (IPv4 and IPv6).
- Public IP: Enabled for access from external sources and for eventual domain setup.
    Load Balancer configuration:
- Load Balancer Name: WebappDBLoadBalancer
- VPC: vpc-01a5c2ecad02a83bc
- Type: Application Load Balancer
- Listener: Port 80 with protocol HTTP.
- Target Group Name: ecs-Databa-RunDatabase
- Protocol: HTTP
- Container to Load Balancer: Backend container, port mapping 5002:5002.
    Health Check Settings:
- Health Check Protocol: HTTP
- Port: 5002
- Path: /health (The application exposes a /health endpoint that returns a 200 OK status if the app is running correctly.)

To add: AWS Secrets Manager credentials injection, Terraform outline!