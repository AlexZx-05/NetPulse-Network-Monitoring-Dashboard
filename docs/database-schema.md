# Database Schema

## Tables

- `organizations`: tenant root, plan metadata.
- `teams`: organization-scoped groups.
- `users`: organization users with role-based access control.
- `devices`: monitored assets such as servers, URLs, routers, APIs, or databases.
- `monitoring_jobs`: scheduled check definitions for ICMP, TCP, HTTP, DNS, SSL, and API checks.
- `metrics`: time-series check results with status, latency, packet loss, and structured detail.
- `incidents`: generated operational events for outages and degradation.
- `alerts`: delivery records for email, Slack, Telegram, and escalation workflows.
- `reports`: generated weekly, monthly, SLA, CSV, and PDF report metadata.
- `api_keys`: hashed programmatic access tokens and scopes.
- `audit_logs`: tenant-scoped administrative and security events.

## Production Notes

- Partition `metrics` by time in high-volume deployments.
- Move long-term metrics to a TSDB or cold object storage after retention windows.
- Use Alembic migrations before production; `create_all` exists only to simplify local startup.
- Add row-level security policies in PostgreSQL for defense in depth when the data model stabilizes.
