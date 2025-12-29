# Security Policy

WhatsNext is designed for trusted internal environments (lab networks, private clusters). It is not hardened for public internet exposure.

## Reporting Vulnerabilities

Email the maintainers directly or use GitHub's "Report a vulnerability" feature. Do not open public issues for security bugs.

## Implemented Measures

### Authentication

- Optional API key authentication via `X-API-Key` header
- Constant-time comparison to prevent timing attacks
- Multiple keys supported (comma-separated in config)

```bash
# .env
api_keys=key1,key2,key3
```

If `api_keys` is unset, authentication is disabled (logged as warning). Generate keys with `openssl rand -base64 32`.

### Rate Limiting

- Per-IP sliding window rate limiting
- Configurable via `rate_limit_per_minute` (0 = disabled)
- Returns `Retry-After` header on limit

State is in-memory per process. For multi-worker or distributed deployments, use a reverse proxy or Redis.

### Input Validation

- Pydantic schema validation on all inputs
- Status enum validation
- Pagination capped at 1000 items
- SQLAlchemy ORM only (no raw SQL)

### CORS

Configurable via `cors_origins`. Default is `*` (all origins). Credentials auto-disabled with wildcard.

## Known Limitations

### High Priority

1. **No HTTPS by default** - Deploy behind a TLS-terminating reverse proxy (nginx, Caddy).

2. **X-Forwarded-For trust** - Rate limiting can be bypassed by header spoofing. Only deploy behind trusted proxies.

3. **Auth disabled by default** - Always set `api_keys` in production.

### Medium Priority

4. **No RBAC** - All authenticated clients have equal access to all projects.

5. **No request signing** - API keys can be intercepted. Use HTTPS.

6. **Client uses HTTP only** - Manually use `https://` URLs until SSL parameter is added.

### Low Priority

7. **OpenAPI docs public** - `/docs` and `/redoc` bypass auth. Disable in production or protect at proxy level.

8. **No audit logging** - No persistent log of auth attempts or operations.

9. **Secrets in env vars** - Use a secrets manager in production.

## Production Checklist

```bash
# .env
api_keys=<key1>,<key2>
rate_limit_per_minute=100
cors_origins=https://your-app.com
```

- Deploy behind HTTPS reverse proxy
- Restrict database access via firewall
- Use secrets manager for credentials
- Enable database SSL
- Set up monitoring and log aggregation
