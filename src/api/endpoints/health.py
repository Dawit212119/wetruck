from fastapi import APIRouter, Depends
from sqlalchemy import text
from app.core.db import get_session  # <- new session dependency
from app.core.app_logging import logger
from sqlalchemy.orm import Session

router = APIRouter()


@router.get("/check")
def health_check(db: Session = Depends(get_session)):
    """
    Simple health check endpoint to verify database connectivity.
    """
    try:
        # Execute a simple SQL query
        result = db.execute(text("SELECT 1"))
        row = result.fetchone()
        logger.info(f"DB connected, result: {row[0]}")
        return {"status": "ok", "db": f"connected, result: {row[0]}"}
    except Exception as e:
        logger.exception("DB connection failed")
        return {"status": "ok", "db": f"error: {str(e)}"}
