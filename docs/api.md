# API Documentation

Base URL: `/api/v1`

Authentication uses `Authorization: Bearer <jwt>`.

## Auth

- `POST /auth/register`
  - Body: `organization_name`, `email`, `full_name`, `password`
  - Returns: JWT access token
- `POST /auth/login`
  - Body: `email`, `password`
  - Returns: JWT access token
- `GET /auth/me`
  - Returns: current user profile

## Monitoring

- `GET /monitoring/summary`
  - Returns device counts, uptime percentage, and average latency.
- `GET /monitoring/devices`
  - Returns tenant devices.
- `POST /monitoring/devices`
  - Roles: owner, admin, engineer
  - Body: `name`, `target`, `tags`
- `GET /monitoring/jobs`
  - Returns monitoring jobs.
- `POST /monitoring/jobs`
  - Roles: owner, admin, engineer
  - Body: `device_id`, `monitor_type`, `interval_seconds`, `timeout_seconds`, `config`
- `POST /monitoring/jobs/{job_id}/run`
  - Executes a check immediately and returns a metric.
- `GET /monitoring/metrics`
  - Returns recent metrics.

## Realtime

- `WS /ws/dashboard?token=<jwt>`
  - Emits dashboard summary JSON every five seconds.

## Incidents

- `GET /incidents`
  - Returns latest incidents.

## Reports

- `GET /reports/sla`
  - Returns 30-day SLA summary.
- `GET /reports/csv`
  - Downloads recent metrics as CSV.
- `GET /reports/pdf`
  - Queues a future PDF report workflow placeholder.

## Admin

- `GET /admin/dashboard`
  - Roles: owner, admin
  - Returns tenant user/device/incident counts.
