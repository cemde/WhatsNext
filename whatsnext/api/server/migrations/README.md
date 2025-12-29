# Database Migrations

This directory contains Alembic database migrations for WhatsNext.

## Quick Reference

```bash
# Apply all pending migrations
alembic upgrade head

# Or use the CLI
whatsnext db upgrade

# Check current migration status
whatsnext db status

# Rollback last migration
whatsnext db downgrade
```

## Creating New Migrations

When you modify `models.py`, create a migration:

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "add user table"

# Review the generated file in versions/
# Then apply it
alembic upgrade head
```

## Migration Files

- `env.py` - Configuration that connects to WhatsNext database settings
- `script.py.mako` - Template for new migration files
- `versions/` - Individual migration scripts

## Best Practices

1. **Always review auto-generated migrations** - Alembic can't detect all changes
2. **Test migrations on a copy of production data** before deploying
3. **Keep migrations small and focused** - one logical change per migration
4. **Never edit a migration that's been applied to production**
