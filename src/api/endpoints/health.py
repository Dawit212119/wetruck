from fastapi import APIRouter, Depends
from sqlalchemy import text
from src.core.db import get_db
from sqlalchemy.orm import Session

router = APIRouter()


@router.get("/check")
def health_check(db: Session = Depends(get_db)):
    """
    Simple health check endpoint to verify database connectivity.
    """
    try:
        # Execute a simple SQL query
        result = db.execute(text("SELECT 1"))
        row = result.fetchone()
        return {"status": "ok", "db": f"connected, result: {row[0]}"}
    except Exception as e:
        return {"status": "ok", "db": f"error: {str(e)}"}
