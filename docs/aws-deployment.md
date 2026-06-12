# AWS Deployment Guide

## EC2 Baseline

1. Launch Ubuntu 24.04 LTS on an EC2 instance.
2. Use at least `t3.medium` for small production pilots.
3. Attach an Elastic IP.
4. Open ports `80` and `443`; restrict `22` to trusted IPs.
5. Store production secrets in AWS Systems Manager Parameter Store or Secrets Manager.

## Bootstrap

Use [deploy/aws/ec2-user-data.sh](../deploy/aws/ec2-user-data.sh) as a starting point. Replace the repository URL and inject production `.env` values.

## Production Hardening

- Terminate TLS with ALB, ACM, or Nginx Certbot.
- Move PostgreSQL to RDS with automated backups and PITR.
- Move Redis to ElastiCache.
- Send container logs to CloudWatch.
- Use IAM instance profiles instead of static AWS credentials.
- Add WAF and rate limits for public API endpoints.
- Run workers on separate instances or ECS services for predictable scaling.

## Scaling

- API: horizontal FastAPI replicas behind ALB.
- Workers: scale Celery workers by monitor volume and check latency.
- Database: add read replicas for reporting; partition metrics.
- Frontend: serve static assets from S3 + CloudFront.
