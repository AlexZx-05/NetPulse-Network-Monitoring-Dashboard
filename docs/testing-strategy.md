# Testing Strategy

## Backend

- Unit test repositories with transaction-scoped test databases.
- Unit test monitoring probes with mocked sockets, DNS, and HTTP clients.
- Integration test FastAPI routes through `TestClient`.
- Contract test API response schemas against frontend DTOs.
- Security test tenant isolation and role enforcement.

## Frontend

- Component tests for dashboard states, empty states, and incident lists.
- API client tests for auth failures and WebSocket reconnect behavior.
- Playwright smoke tests for login, dashboard rendering, and responsive layout.

## Infrastructure

- CI runs backend tests and frontend builds on every PR.
- Add image scanning with Trivy or Grype.
- Add Docker Compose smoke test that registers a tenant, creates a device, creates a job, and runs a check.

## Load and Reliability

- Synthetic load for high-cardinality metrics ingestion.
- Worker soak tests with thousands of jobs.
- Chaos tests for Redis/Postgres outages and alert-channel failures.
