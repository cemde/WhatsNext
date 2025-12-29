# Security Policy

This document describes security considerations for WhatsNext, what protections are in place, and known limitations.

## Reporting Vulnerabilities

If you discover a security vulnerability, please report it by:

1. **Email**: Send details to the maintainers (do not open a public issue)
2. **GitHub Security Advisory**: Use the "Report a vulnerability" feature in the Security tab

Please include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

We aim to respond within 48 hours and will work with you to understand and address the issue.

---

## Security Model

WhatsNext is designed for **trusted environments** such as:
- Internal lab networks
- Private cloud deployments
- Research computing clusters

It is **not designed** for public internet exposure without additional hardening.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Trust Boundary                            │
│                                                             │
│  ┌─────────────┐         ┌─────────────┐                    │
│  │   Clients   │  HTTP   │   Server    │                    │
│  │  (trusted)  │────────►│   (API)     │                    │
│  └─────────────┘         └──────┬──────┘                    │
│                                 │                            │
│                          ┌──────▼──────┐                    │
│                          │ PostgreSQL  │                    │
│                          │ (internal)  │                    │
│                          └─────────────┘                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Implemented Security Measures

### Authentication

| Feature | Status | Notes |
|---------|--------|-------|
| API Key Authentication | ✅ Implemented | Optional, via `X-API-Key` header |
| Constant-time key comparison | ✅ Implemented | Prevents timing attacks |
| Multiple API keys | ✅ Implemented | Comma-separated in config |
| Key rotation | ⚠️ Manual | Requires config update and restart |

**Configuration:**
```bash
# .env file
api_keys=key1,key2,key3
```

**Security notes:**
- If `api_keys` is not set, authentication is **disabled** (server logs a warning)
- API keys are transmitted in headers; use HTTPS in production
- Generate strong keys: `openssl rand -base64 32`

### Rate Limiting

| Feature | Status | Notes |
|---------|--------|-------|
| Per-IP rate limiting | ✅ Implemented | Sliding window algorithm |
| Configurable limits | ✅ Implemented | `rate_limit_per_minute` setting |
| Retry-After header | ✅ Implemented | RFC 7231 compliant |

**Limitations:**
- Rate limit state is **in-memory per process**
- In multi-worker deployments, effective rate is multiplied by worker count
- For distributed rate limiting, use a reverse proxy (nginx, Cloudflare) or Redis

**Configuration:**
```bash
# .env file
rate_limit_per_minute=100  # 0 = disabled (not recommended)
```

### Input Validation

| Feature | Status | Notes |
|---------|--------|-------|
| Pydantic schema validation | ✅ Implemented | All API inputs validated |
| Status enum validation | ✅ Implemented | Rejects invalid status values |
| Pagination limits | ✅ Implemented | Max 1000 items per request |
| Client ID validation | ✅ Implemented | Alphanumeric, max 128 chars |
| SQL injection prevention | ✅ Implemented | SQLAlchemy ORM only, no raw SQL |

### CORS (Cross-Origin Resource Sharing)

| Feature | Status | Notes |
|---------|--------|-------|
| Configurable origins | ✅ Implemented | `cors_origins` setting |
| Credentials protection | ✅ Implemented | Auto-disabled with wildcard origins |

**Security notes:**
- Default allows all origins (`*`) for development convenience
- In production, set specific origins: `cors_origins=https://your-app.com`
- Credentials are automatically disabled if origins = `*`

### Database Security

| Feature | Status | Notes |
|---------|--------|-------|
| Connection pooling | ✅ Implemented | Prevents connection exhaustion |
| Connection validation | ✅ Implemented | `pool_pre_ping` enabled |
| Parameterized queries | ✅ Implemented | SQLAlchemy ORM prevents SQL injection |
| Credential storage | ⚠️ Environment vars | Use secrets manager in production |

---

## Known Limitations & Recommendations

### HIGH Priority

#### 1. No HTTPS by Default

**Risk:** API keys and data transmitted in plaintext.

**Mitigation:**
- Deploy behind a reverse proxy (nginx, Caddy) with TLS termination
- Use a load balancer with SSL (AWS ALB, GCP Load Balancer)
- See [Deployment Guide](docs/getting-started/deployment.md) for nginx setup

#### 2. X-Forwarded-For Header Trust

**Risk:** Rate limiting can be bypassed by spoofing the `X-Forwarded-For` header.

**Current behavior:** Server trusts the first IP in `X-Forwarded-For`.

**Mitigation:**
- Only deploy behind a trusted reverse proxy that overwrites this header
- Configure your proxy to set the real client IP
- For direct exposure, rate limiting should be done at the network level

#### 3. Authentication Disabled by Default

**Risk:** If `api_keys` is not configured, all endpoints are publicly accessible.

**Mitigation:**
- Always set `api_keys` in production
- Server logs a warning at startup if auth is disabled
- Consider requiring explicit `DISABLE_AUTH=true` to run without auth

### MEDIUM Priority

#### 4. No User/Role-Based Access Control

**Current state:** All authenticated clients have equal access to all projects.

**Recommendation for future:**
- Add user accounts with project-level permissions
- Implement read-only vs read-write API keys
- Add audit logging for sensitive operations

#### 5. No Request Signing

**Risk:** API keys can be intercepted and reused.

**Mitigation:**
- Use HTTPS (see #1)
- Implement short-lived tokens or request signing for high-security environments

#### 6. Client Library Uses HTTP Only

**File:** `whatsnext/api/client/server.py`

**Risk:** Client library defaults to HTTP, not HTTPS.

**Workaround:** Manually construct URLs with `https://` or modify the client.

**Future improvement:** Add `use_ssl=True` parameter to `Server` class.

### LOW Priority

#### 7. OpenAPI Documentation Publicly Accessible

**Current behavior:** `/docs`, `/redoc`, `/openapi.json` are excluded from authentication.

**Risk:** API schema visible to unauthenticated users.

**Mitigation for production:**
- Remove docs endpoints: `app = FastAPI(docs_url=None, redoc_url=None)`
- Or add authentication at the reverse proxy level

#### 8. No Audit Logging

**Current state:** No persistent logging of authentication attempts or API operations.

**Recommendation:**
- Add structured logging for security events
- Log failed authentication attempts
- Consider integration with SIEM systems

#### 9. Secrets in Environment Variables

**Current state:** Database passwords and API keys stored in `.env` files.

**Recommendation for production:**
- Use a secrets manager (HashiCorp Vault, AWS Secrets Manager, etc.)
- Never commit `.env` files to version control
- Rotate credentials regularly

---

## Security Configuration Checklist

### Development

```bash
# Minimal security for local development
database_hostname=localhost
database_port=5432
database_user=postgres
database_password=postgres
database_name=whatsnext
# No api_keys = open access (OK for localhost)
```

### Production

```bash
# Production security configuration
database_hostname=your-db-host
database_port=5432
database_user=whatsnext_prod
database_password=<strong-random-password>
database_name=whatsnext_prod

# Authentication (required)
api_keys=<key1>,<key2>

# Rate limiting (recommended)
rate_limit_per_minute=100

# CORS (restrict to your domains)
cors_origins=https://your-app.com,https://admin.your-app.com
cors_allow_credentials=false
```

### Infrastructure Checklist

- [ ] Deploy behind HTTPS reverse proxy
- [ ] Configure firewall to restrict database access
- [ ] Set up log aggregation
- [ ] Enable database connection encryption (SSL)
- [ ] Use secrets manager for credentials
- [ ] Set up monitoring and alerting
- [ ] Regular security updates for dependencies
- [ ] Backup strategy for database

---

## Dependency Security

### Monitoring

We recommend using automated dependency scanning:

```bash
# Check for known vulnerabilities
pip install pip-audit
pip-audit

# Or use GitHub's Dependabot (enabled by default)
```

### Key Dependencies

| Package | Purpose | Security Notes |
|---------|---------|----------------|
| FastAPI | Web framework | Active security maintenance |
| SQLAlchemy | Database ORM | Parameterized queries prevent SQL injection |
| Pydantic | Validation | Input validation and sanitization |
| uvicorn | ASGI server | Production-ready, but use with proxy |
| psycopg2 | PostgreSQL driver | Use `psycopg2` (not `-binary`) in production |

---

## Security Updates

| Date | Version | Description |
|------|---------|-------------|
| 2025-12-29 | 0.0.1 | Initial security review and hardening |

---

## Questions?

For security-related questions that are not vulnerabilities, please open a GitHub Discussion.
