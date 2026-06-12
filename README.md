# NetPulse

NetPulse is a production-grade SaaS foundation for real-time network observability. It monitors websites, APIs, TCP services, DNS, SSL certificates, and device health for multi-tenant organizations.

## Quick Start

```bash
cp .env.example .env
docker compose up --build
```

Services:

- Frontend: http://localhost:3000
- API: http://localhost:8000
- API docs: http://localhost:8000/docs
- Reverse proxy: http://localhost

Create the first tenant with `POST /api/v1/auth/register`, then use the returned JWT in the frontend or API.

## Architecture

See [docs/architecture.md](docs/architecture.md).

## API

See [docs/api.md](docs/api.md).

## Deployment

See [docs/aws-deployment.md](docs/aws-deployment.md).
