from logging.config import fileConfig
from alembic import context
from sqlalchemy import engine_from_config, pool
import os
from dotenv import load_dotenv

# Load .env
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(BASE_DIR, ".env"))

from src.core.db.session import Base
from src.models import models  # noqa

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_database_url() -> str:
    user = os.environ["DB_USERNAME"]
    password = os.environ.get("DB_PASSWORD", "")
    host = os.environ["DB_HOST"]
    port = os.environ["DB_PORT"]
    db = os.environ["DB_NAME"]

    if password:
        return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"
    else:
        return f"postgresql+psycopg2://{user}@{host}:{port}/{db}"


def run_migrations_offline():
    context.configure(
        url=get_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = get_database_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
