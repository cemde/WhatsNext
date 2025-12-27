# Configuration Guide

This guide covers all configuration options for the WhatsNext server.

## Configuration File

WhatsNext uses a `.env` file for configuration. Create this file in the directory where you run the server.

```bash title=".env"
# Required: Database Connection
database_hostname=localhost
database_port=5432
database_user=postgres
database_password=your_secure_password
database_name=whatsnext

# Optional: Security
api_keys=key1,key2,key3

# Optional: CORS
cors_origins=*
cors_allow_credentials=true
cors_allow_methods=*
cors_allow_headers=*

# Optional: Rate Limiting
rate_limit_per_minute=0
```

## Database Configuration

### Required Settings

| Setting | Description | Example |
|---------|-------------|---------|
| `database_hostname` | PostgreSQL server address | `localhost` |
| `database_port` | PostgreSQL port | `5432` |
| `database_user` | Database username | `postgres` |
| `database_password` | Database password | `secret123` |
| `database_name` | Database name | `whatsnext` |

### Example Configurations

=== "Local Development"

    ```bash
    database_hostname=localhost
    database_port=5432
    database_user=postgres
    database_password=postgres
    database_name=whatsnext_dev
    ```

=== "Docker PostgreSQL"

    ```bash
    database_hostname=postgres
    database_port=5432
    database_user=whatsnext
    database_password=secure_password_here
    database_name=whatsnext
    ```

=== "Cloud Database"

    ```bash
    database_hostname=my-db.us-east-1.rds.amazonaws.com
    database_port=5432
    database_user=whatsnext_admin
    database_password=very_secure_password
    database_name=whatsnext_production
    ```

## Authentication

By default, the API is open (no authentication required). For production, enable API key authentication.

### Enabling API Keys

Add API keys to your `.env` file:

```bash title=".env"
# Single API key
api_keys=my-secret-api-key-12345

# Multiple API keys (comma-separated)
api_keys=key-for-team-a,key-for-team-b,key-for-admin
```

### Using API Keys in Clients

When authentication is enabled, all API requests must include the `X-API-Key` header:

```python
import requests

# Direct API calls
response = requests.get(
    "http://localhost:8000/projects/",
    headers={"X-API-Key": "my-secret-api-key-12345"}
)
```

!!! note "Client Library Support"
    The Python client library will support API keys in a future version. For now, use direct HTTP requests with the API key header.

### Excluded Endpoints

These endpoints don't require authentication (for health checks):

- `GET /` - Connection check
- `GET /checkdb` - Database health check
- `GET /docs` - API documentation
- `GET /openapi.json` - OpenAPI schema
- `GET /redoc` - Alternative docs

### Generating Secure API Keys

```python
import secrets

# Generate a secure 32-character API key
api_key = secrets.token_urlsafe(24)
print(f"Your API key: {api_key}")
```

Or use the command line:

```bash
# Linux/macOS
openssl rand -base64 24

# Output: something like "K8j2mN4pQ1rS5tU8vW0xY3zA6bC9dE"
```

## CORS (Cross-Origin Resource Sharing)

CORS settings control which web browsers can access your API.

### Settings

| Setting | Description | Default |
|---------|-------------|---------|
| `cors_origins` | Allowed origins | `*` (all) |
| `cors_allow_credentials` | Allow cookies | `true` |
| `cors_allow_methods` | Allowed HTTP methods | `*` (all) |
| `cors_allow_headers` | Allowed headers | `*` (all) |

### Example Configurations

=== "Allow All (Development)"

    ```bash
    cors_origins=*
    cors_allow_credentials=true
    cors_allow_methods=*
    cors_allow_headers=*
    ```

=== "Specific Origins (Production)"

    ```bash
    cors_origins=https://myapp.com,https://admin.myapp.com
    cors_allow_credentials=true
    cors_allow_methods=GET,POST,PUT,DELETE
    cors_allow_headers=Content-Type,X-API-Key
    ```

=== "Locked Down"

    ```bash
    cors_origins=https://myapp.com
    cors_allow_credentials=false
    cors_allow_methods=GET,POST
    cors_allow_headers=Content-Type,X-API-Key
    ```

## Rate Limiting

Protect your API from abuse by limiting requests per client.

### Settings

| Setting | Description | Default |
|---------|-------------|---------|
| `rate_limit_per_minute` | Max requests per minute per IP | `0` (disabled) |

### Enabling Rate Limiting

```bash title=".env"
# Allow 100 requests per minute per IP
rate_limit_per_minute=100
```

### How It Works

- Limits are per client IP address
- Uses a sliding window algorithm
- Returns `429 Too Many Requests` when limit exceeded
- Includes `Retry-After` header with seconds to wait

### Example Response When Rate Limited

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 45
Content-Type: text/plain

Rate limit exceeded. Try again in 45 seconds.
```

## Complete Configuration Examples

### Development Environment

```bash title=".env"
# Database (local PostgreSQL)
database_hostname=localhost
database_port=5432
database_user=postgres
database_password=postgres
database_name=whatsnext_dev

# No authentication (open API)
# api_keys=

# Allow all CORS
cors_origins=*

# No rate limiting
rate_limit_per_minute=0
```

### Production Environment

```bash title=".env"
# Database (production PostgreSQL)
database_hostname=db.internal.mycompany.com
database_port=5432
database_user=whatsnext_prod
database_password=super_secure_password_here
database_name=whatsnext

# API authentication
api_keys=prod-key-team-a-abc123,prod-key-team-b-def456,prod-key-admin-xyz789

# Restricted CORS
cors_origins=https://jobs.mycompany.com
cors_allow_credentials=true
cors_allow_methods=GET,POST,PUT,DELETE
cors_allow_headers=Content-Type,X-API-Key,Authorization

# Rate limiting
rate_limit_per_minute=60
```

### High-Security Environment

```bash title=".env"
# Database
database_hostname=secure-db.private.vpc
database_port=5432
database_user=whatsnext_secure
database_password=extremely_long_random_password_here_abc123xyz
database_name=whatsnext_secure

# Single admin key only
api_keys=admin-only-key-with-very-long-random-string

# Very restricted CORS
cors_origins=https://internal-admin.mycompany.com
cors_allow_credentials=false
cors_allow_methods=GET,POST
cors_allow_headers=X-API-Key

# Strict rate limiting
rate_limit_per_minute=30
```

## Environment Variables vs .env File

You can also set configuration via environment variables directly:

```bash
# Using environment variables
export database_hostname=localhost
export database_port=5432
export database_user=postgres
export database_password=secret
export database_name=whatsnext
export api_keys=my-api-key

# Start server
uvicorn whatsnext.api.server.main:app
```

The `.env` file is loaded automatically if present. Environment variables override `.env` values.

## Troubleshooting

### "pydantic_settings" error

Make sure you have the server dependencies installed:

```bash
pip install whatsnext[server]
# or
pip install pydantic-settings
```

### Database connection errors

1. Check PostgreSQL is running:
   ```bash
   pg_isready -h localhost -p 5432
   ```

2. Verify credentials work:
   ```bash
   psql -h localhost -U postgres -d whatsnext
   ```

3. Check your `.env` file has no typos

### CORS errors in browser

If you see CORS errors in browser console:

1. Check `cors_origins` includes your frontend URL
2. Make sure the URL includes protocol (`https://`)
3. Don't include trailing slashes

### Rate limit too strict

If legitimate clients are being rate limited:

1. Increase `rate_limit_per_minute`
2. Consider using a load balancer with multiple server instances
3. Use different API keys for different clients (future feature)
