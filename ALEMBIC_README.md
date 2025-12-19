# Alembic Usage Guide

This guide outlines how to set up, create, and apply migrations using **Alembic**, a lightweight database migration tool for SQLAlchemy.

---

## Prerequisites

1. Python installed (`>= 3.7` recommended).
2. Alembic installed in your environment:
   ```bash
   pip install alembic
   ```

3. A configured database (e.g., PostgreSQL, SQLite, etc.).

---

## Step 1: Initialize Alembic

To set up Alembic for your project:

1. Navigate to your project directory.
2. Run:
   ```bash
   alembic init alembic
   ```
   This creates an `alembic` directory with the following structure:
   ```
   alembic/
       env.py
       script.py.mako
       versions/   # Directory for migration files
   alembic.ini    # Main configuration file
   ```

3. Configure your database URL in **`alembic.ini`**:
   ```ini
   sqlalchemy.url = postgresql+psycopg2://<username>:<password>@<host>:<port>/<database_name>
   ```
   Alternatively, use environment variables for sensitive data.

---

## Step 2: Update `env.py`

Edit `alembic/env.py` to include your models:

1. Import your `Base` (SQLAlchemy models).
   ```python
   from app.db.base import Base
   ```

2. Update the `target_metadata` variable to reference your `Base`:
   ```python
   target_metadata = Base.metadata
   ```
3. Update `alembic/env.py` add models
   ```python
   from app.db.session import Base
   
   from app.models.notification import Notification
   from app.models.customer import Customer
   from app.models.group import Group
   from app.models.group_customer import GroupCustomer
   from app.models.notification_receipt import NotificationReceipt
   from app.models.message import Message
   
   target_metadata = Base.metadata```
4. Update `alembic/env.py` add postgres db connection string from `setting`. Override `sqlalchemy.url` `/on alembic.ini`
   ```python
   DATABASE_URL = (
    f"postgresql+psycopg2://{settings.postgres_username}:{settings.postgres_password}"
    f"@{settings.postgres_url}:{settings.postgres_port}/{settings.postgres_database_name}"
   )

   config = context.config
   config.set_main_option("sqlalchemy.url", DATABASE_URL)  # Set the database URL

   def run_migrations_offline() -> None:```
---


## Step 3: Create a Migration Script

To create a new migration based on changes to your models:

1. Run:
   ```bash
   alembic revision --autogenerate -m "Description of the migration"
   ```
   This generates a new file in the `alembic/versions/` folder.

2. Review the generated file and verify that the changes match your model updates.

---

## Step 4: Apply Migrations

To apply the migration(s) to your database:

1. Run:
   ```bash
   alembic upgrade head
   ```
   This applies all pending migrations.

---

## Step 5: Downgrade (Optional)

To revert to a previous migration:

1. Run:
   ```bash
   alembic downgrade <revision>
   ```
   Example: Revert one step:
   ```bash
   alembic downgrade -1
   ```

---

## Useful Alembic Commands

1. **Check current version**:
   ```bash
   alembic current
   ```

2. **Show revision history**:
   ```bash
   alembic history
   ```

3. **Stamp a database with a specific revision** (without applying it):
   ```bash
   alembic stamp head
   ```

4. **Manually edit a migration script**:
   Go to the `alembic/versions/` folder, open the desired script, and modify it.

---

## Example Workflow

1. Modify your SQLAlchemy models in your `app/models/` directory.
2. Create a migration:
   ```bash
   alembic revision --autogenerate -m "Added new column to customers"
   ```
3. Apply the migration:
   ```bash
   alembic upgrade head
   ```

4. Verify the changes in your database.

---

## Troubleshooting

1. **Error: `target_metadata is None`**:
   Ensure `Base.metadata` is properly imported and assigned in `env.py`.

2. **Error: Database not found**:
   Verify your database URL in `alembic.ini` or environment variables.

3. **Need to reset migrations**:
   - Clear the `alembic/versions/` folder.
   - Delete tables created by Alembic (like `alembic_version`).
   - Restart the process from **Step 3**.