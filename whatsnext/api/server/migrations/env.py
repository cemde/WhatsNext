"""Alembic migration environment configuration.

This file configures Alembic to use the same database settings as the WhatsNext server.
Database URL is loaded from environment variables or .env file.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Import the WhatsNext models and database configuration
# Note: models import is required for Alembic autogenerate to detect model changes
from whatsnext.api.server import models as _models  # noqa: F401
from whatsnext.api.server.config import db
from whatsnext.api.server.database import Base

# Alembic Config object - provides access to alembic.ini values
config = context.config

# Set up Python logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set the target metadata for autogenerate support
# This tells Alembic about all our SQLAlchemy models
target_metadata = Base.metadata

# Build database URL from WhatsNext configuration
# This ensures migrations use the same database as the server
DATABASE_URL = f"postgresql://{db.user}:{db.password}@{db.hostname}:{db.port}/{db.database}"


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This generates SQL scripts without connecting to the database.
    Useful for reviewing changes before applying them.

    Usage: alembic upgrade head --sql
    """
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    This connects to the database and applies migrations directly.
    """
    # Create engine configuration
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = DATABASE_URL

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # Compare types to detect column type changes
            compare_type=True,
            # Compare server defaults
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


# Run the appropriate migration mode
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
