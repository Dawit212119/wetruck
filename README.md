# Platform Backend

A FastAPI boilerplate application with database integration, middleware, and API endpoints.

## Prerequisites

- Python 3.8+
- PostgreSQL database
- pip (Python package manager)

## Setup Instructions

### 1. Install Dependencies

Create a virtual environment (recommended):

```bash
python -m venv venv
```

Activate the virtual environment:

- **Windows:**
  ```bash
  venv\Scripts\activate
  ```

- **macOS/Linux:**
  ```bash
  source venv/bin/activate
  ```

Install required packages:

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the root directory (copy from `.env.example`):

```bash
# Environment Configuration
ENV=LOCAL

# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_database_name
DB_USERNAME=your_username
DB_PASSWORD=your_password
```

Update the database credentials with your PostgreSQL connection details.

### 3. Set Up Database

Make sure PostgreSQL is running and create a database:

```sql
CREATE DATABASE your_database_name;
```

Run database migrations using Alembic:

```bash
alembic upgrade head
```

### 4. Run the Application

From the root directory, run:

```bash
uvicorn src.main:app --reload
```

Or if you're in the `platform-backend` directory:

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

The application will be available at:
- API: `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`
- Alternative Docs: `http://localhost:8000/redoc`

### 5. Test the Health Endpoint

Visit: `http://localhost:8000/health/check`

This will verify that the application and database connection are working correctly.

## Project Structure

```
platform-backend/
├── src/
│   ├── api/              # API routes and endpoints
│   ├── core/             # Core functionality (settings, db, exceptions)
│   ├── middlewares/      # Custom middleware
│   ├── models/           # Database models
│   └── main.py           # Application entry point
├── alembic/              # Database migrations
├── requirements.txt      # Python dependencies
└── .env                  # Environment variables (create this)
```

## Development

- The application uses FastAPI with SQLAlchemy for database ORM
- Alembic is used for database migrations
- Environment-based configuration (LOCAL, DEV, PROD)
- CORS middleware configured for development

## Troubleshooting

- **Import errors**: Make sure you're running from the correct directory and all dependencies are installed
- **Database connection errors**: Verify your `.env` file has correct database credentials
- **Port already in use**: Change the port using `--port` flag, e.g., `--port 8001` 
