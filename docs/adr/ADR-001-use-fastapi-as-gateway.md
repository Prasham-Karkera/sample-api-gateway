# ADR-001: Use FastAPI as the API Gateway Framework

**Status:** ACCEPTED  
**Date:** 2026-01-15  
**Author(s):** @prasham-dev  
**Deciders:** @prasham-dev, @platform-lead  

---

## Context

We needed to choose a framework for the FleetBite API Gateway. Key requirements:
- Must support async I/O for high-throughput proxying
- Must be able to validate and decode JWTs efficiently
- Must expose Prometheus metrics easily
- Must auto-generate OpenAPI documentation
- Should be easy to test and maintain

The team evaluated FastAPI, Kong (OSS), nginx + Lua, and Traefik.

## Decision

Use **FastAPI** (Python 3.12) as the API Gateway implementation rather than an off-the-shelf gateway.

## Rationale

A custom FastAPI gateway gives us full control over authentication logic, rate limiting behavior, header manipulation, and request transformation — none of which are trivial to configure in Kong or Traefik without paid enterprise plugins.

### Alternatives Considered

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| FastAPI (custom) | Full control, typed, OpenAPI auto-gen, team familiarity | We own maintenance | ✅ Selected |
| Kong OSS | Mature, plugin ecosystem | Complex to configure, Lua for custom logic, infra overhead | ❌ Rejected |
| nginx + Lua | Very fast, battle-tested | Lua is unfamiliar, hard to test, poor observability | ❌ Rejected |
| Traefik | Good k8s integration | Limited auth customization without middleware | ❌ Rejected |

## Consequences

**Positive:**
- Full type safety and mypy checking for all gateway logic
- Auto-generated OpenAPI spec for the gateway itself
- Easy to unit test with httpx AsyncClient
- Consistent technology stack across all FleetBite services

**Negative:**
- We own the rate-limiting implementation (currently in-memory; Redis needed at scale)
- We must maintain the route table manually when services are added

## Implementation Notes

- Route table in `app/routers/proxy.py` must be updated when new services are added
- In-memory rate limiter is sufficient for MVP; use Redis with `slowapi` library for production scale
- Upgrade plan documented in [ADR-002-redis-rate-limiting.md]

## References

- [FastAPI docs](https://fastapi.tiangolo.com)
- [httpx async client](https://www.python-httpx.org)
- [Conventional Commits — ENGINEERING_STANDARDS.md §1](../../ENGINEERING_STANDARDS.md)
