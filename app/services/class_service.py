"""Class management service — business logic for class CRUD."""

from typing import List

from fastapi import UploadFile
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, ForbiddenException, NotFoundException
from app.models.models import Class, ClassRoster
from app.repositories.class_repository import ClassRepository
from app.schemas.schemas import ClassCreateRequest, ClassResponse


class ClassService:
    """Service handling class management for teachers."""

    def __init__(self, db: AsyncSession):
        self.class_repo = ClassRepository(db)

    async def create_class(
        self, data: ClassCreateRequest, teacher_id: int
    ) -> ClassResponse:
        """Create a new class owned by the teacher."""
        class_ = Class(
            name=data.name,
            teacher_id=teacher_id,
        )
        class_ = await self.class_repo.create(class_)
        return ClassResponse.model_validate(class_)

    async def get_teacher_classes(self, teacher_id: int) -> List[ClassResponse]:
        """Get all classes owned by a teacher."""
        classes = await self.class_repo.get_by_teacher(teacher_id)
        return [ClassResponse.model_validate(c) for c in classes]

    async def get_class_by_id(
        self, class_id: int, teacher_id: int
    ) -> ClassResponse:
        """Get a specific class, validating teacher ownership."""
        class_ = await self.class_repo.get_by_id(class_id)
        if not class_:
            raise NotFoundException(detail="Class not found")
        if class_.teacher_id != teacher_id:
            raise ForbiddenException(detail="You do not own this class")
        return ClassResponse.model_validate(class_)

    async def verify_class_ownership(self, class_id: int, teacher_id: int) -> Class:
        """Verify a teacher owns a class and return the Class model.

        Used internally by other services that need the raw model.
        """
        class_ = await self.class_repo.get_by_id(class_id)
        if not class_:
            raise NotFoundException(detail="Class not found")
        if class_.teacher_id != teacher_id:
            raise ForbiddenException(detail="You do not own this class")
        return class_

    async def upload_roster(self, class_id: int, teacher_id: int, file: UploadFile) -> dict:
        """Upload and parse a CSV roster for a class."""
        import csv
        import io
        
        await self.verify_class_ownership(class_id, teacher_id)

        if not file.filename.endswith(".csv"):
            raise BadRequestException(detail="Only CSV files are supported")

        try:
            content = await file.read()
            decoded_content = content.decode("utf-8")
            reader = csv.DictReader(io.StringIO(decoded_content))
            
            # Identify columns
            fieldnames = reader.fieldnames or []
            name_col = next((col for col in fieldnames if "name" in col.lower()), None)
            email_col = next((col for col in fieldnames if "email" in col.lower()), None)

            if not name_col or not email_col:
                raise BadRequestException(detail="CSV must contain 'name' and 'email' columns")

            # First, delete existing roster for this class
            await self.class_repo.db.execute(
                delete(ClassRoster).where(ClassRoster.class_id == class_id)
            )

            # Insert new students
            roster_entries = []
            for row in reader:
                name = row.get(name_col, "").strip()
                email = row.get(email_col, "").strip()
                if name and email:
                    roster_entries.append(
                        ClassRoster(
                            class_id=class_id,
                            student_name=name,
                            student_email=email
                        )
                    )
            
            if not roster_entries:
                raise BadRequestException(detail="No valid students found in the CSV")

            self.class_repo.db.add_all(roster_entries)
            await self.class_repo.db.commit()

            return {"success": True, "message": f"Successfully enrolled {len(roster_entries)} students"}
            
        except Exception as e:
            await self.class_repo.db.rollback()
            if isinstance(e, BadRequestException):
                raise e
            raise BadRequestException(detail=f"Failed to process CSV file: {str(e)}")
