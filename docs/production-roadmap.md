# Production Roadmap

This repository is a production-grade foundation. Before using it for regulated or high-scale enterprise workloads, complete these items:

- Replace `Base.metadata.create_all` with Alembic migrations.
- Add refresh tokens, session revocation, MFA, and password reset tokens.
- Add alert escalation policies, schedules, deduplication, and notification retries.
- Add metric retention jobs and time partitioning.
- Add API key creation endpoints with one-time secret display.
- Add OpenTelemetry tracing across API and workers.
- Add Redis-backed WebSocket fanout for multi-replica deployments.
- Add RDS, ElastiCache, and ECS/Terraform deployment modules.
