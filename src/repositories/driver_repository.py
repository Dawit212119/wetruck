from src.repositories.base_repository import BaseRepository
from sqlalchemy import select, or_
from src.models.models import Driver

class DriverRepository(BaseRepository[Driver]):
    model = Driver

    async def is_already_exist(
        self, license_number: str = None, phone_number: str = None, email: str = None
    ):
        """
        Check if a driver already exists based on license, phone, or email.
        Returns the first matching driver or None.
        """
        if not (license_number or phone_number or email):
            return None

        match_conditions = []
        if license_number:
            match_conditions.append(self.model.driver_license_number == license_number)
        if phone_number:
            match_conditions.append(self.model.phone_number == phone_number)
        if email:
            match_conditions.append(self.model.email == email)

        stmt = select(self.model).where(or_(*match_conditions))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
