from fastapi import APIRouter, Depends
from sqlalchemy import text
from src.core.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Health check endpoint to verify database connectivity.
    """
    try:
        # Execute a simple SQL query
        result = await db.execute(text("SELECT 1"))
        row = result.fetchone()
        return {"status": "ok", "db": f"connected, result: {row[0]}"}
    except Exception as e:
        return {"status": "ok", "db": f"error: {str(e)}"}
