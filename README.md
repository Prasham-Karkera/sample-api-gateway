# ka-chow-api-gateway

> **Service:** API Gateway & Auth  
> **Port:** 8000  
> **Team:** Platform Engineering  
> **Status:** Active

## Service Overview

The API Gateway is the single entry point for all external traffic into the FleetBite platform. It handles JWT authentication, per-IP rate limiting, and reverse-proxy routing to downstream microservices. No business logic lives here — it is purely a traffic management and security layer.

## Architecture Role

```
Internet ──► [API Gateway :8000] ──► user-service    :8001
                                 ──► order-service   :8002
                                 ──► inventory-service :8003
                                 ──► notification-service :8004
```

All client requests **must** flow through the gateway. Service-to-service calls bypass the gateway and communicate directly.

## Dependencies

| Service | Type | Purpose |
|---------|------|---------|
| user-service | Downstream | Routes `/v1/users/*` and `/v1/auth/*` |
| order-service | Downstream | Routes `/v1/orders/*` |
| inventory-service | Downstream | Routes `/v1/items/*`, `/v1/stock/*` |
| notification-service | Downstream | Routes `/v1/events/*` |

## API Reference

Full OpenAPI spec: [`docs/openapi.yaml`](docs/openapi.yaml)

### Route Table

| Path Prefix | Upstream Service |
|-------------|----------------|
| `/v1/users/*` | user-service |
| `/v1/auth/*` | user-service |
| `/v1/orders/*` | order-service |
| `/v1/items/*` | inventory-service |
| `/v1/stock/*` | inventory-service |
| `/v1/events/*` | notification-service |

### Auth-Excluded Paths

These paths are accessible without a JWT token:
- `GET /health/live`
- `GET /health/ready`
- `GET /metrics`
- `POST /v1/auth/token`
- `POST /v1/users/register`

## Configuration

Copy `.env.example` to `.env` for local development:

| Variable | Default | Description |
|----------|---------|-------------|
| `GW_ENV` | `development` | Environment name |
| `GW_JWT_SECRET_KEY` | *(required)* | 256-bit JWT signing secret |
| `GW_JWT_ALGORITHM` | `HS256` | JWT algorithm |
| `GW_JWT_EXPIRY_SECONDS` | `3600` | Token TTL in seconds |
| `GW_RATE_LIMIT_RPM` | `120` | Requests per minute per IP |
| `GW_HTTP_TIMEOUT` | `10.0` | Upstream request timeout (sec) |
| `GW_USER_SERVICE_URL` | `http://user-service:8001` | user-service base URL |
| `GW_ORDER_SERVICE_URL` | `http://order-service:8002` | order-service base URL |
| `GW_INVENTORY_SERVICE_URL` | `http://inventory-service:8003` | inventory-service base URL |
| `GW_NOTIFICATION_SERVICE_URL` | `http://notification-service:8004` | notification-service base URL |

## Running Locally

**Prerequisites:** Docker, docker-compose

```bash
# Copy env file
cp .env.example .env

# Start all services (requires other service images)
docker-compose up -d

# View logs
docker-compose logs -f api-gateway

# Test
curl http://localhost:8000/health/live
```

## Running Tests

```bash
pip install -e ".[dev]"
pytest --cov=app tests/
```

## Deployment

```bash
# Apply k8s manifests
kubectl apply -f k8s/manifests.yaml -n fleetbite-production

# Monitor rollout
kubectl rollout status deployment/api-gateway -n fleetbite-production
```

## Runbook Links

- [Gateway Outage Runbook](https://wiki.fleetbite.internal/runbooks/api-gateway-outage)
- [Rate Limit Tuning Guide](https://wiki.fleetbite.internal/runbooks/rate-limit-tuning)

## CHANGELOG

See [CHANGELOG.md](CHANGELOG.md).
