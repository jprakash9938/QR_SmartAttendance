"""Class management API routes.

Endpoints:
  POST /api/v1/classes            — Create a class (teacher only)
  GET  /api/v1/classes            — List teacher's classes
  GET  /api/v1/classes/{class_id} — Get class details
"""

from typing import List

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import require_teacher
from app.models.models import User
from app.schemas.schemas import ClassCreateRequest, ClassResponse
from app.services.class_service import ClassService

router = APIRouter(prefix="/api/v1/classes", tags=["Classes"])


@router.post(
    "",
    response_model=ClassResponse,
    status_code=201,
    summary="Create a class",
    description="Create a new class. Only teachers can create classes.",
    responses={
        201: {"description": "Class created successfully"},
        403: {"description": "Teacher access required"},
        422: {"description": "Validation error"},
    },
)
async def create_class(
    data: ClassCreateRequest,
    teacher: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db),
):
    """Create a new class (teacher only)."""
    service = ClassService(db)
    return await service.create_class(data, teacher.id)


@router.get(
    "",
    response_model=List[ClassResponse],
    summary="List classes",
    description="Get all classes owned by the authenticated teacher.",
    responses={
        200: {"description": "List of classes"},
        403: {"description": "Teacher access required"},
    },
)
async def list_classes(
    teacher: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db),
):
    """List all classes for the authenticated teacher."""
    service = ClassService(db)
    return await service.get_teacher_classes(teacher.id)


@router.get(
    "/{class_id}",
    response_model=ClassResponse,
    summary="Get class details",
    description="Get details of a specific class. Teacher must own the class.",
    responses={
        200: {"description": "Class details"},
        403: {"description": "Not the class owner"},
        404: {"description": "Class not found"},
    },
)
async def get_class(
    class_id: int,
    teacher: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db),
):
    """Get class details (teacher only, must own the class)."""
    service = ClassService(db)
    return await service.get_class_by_id(class_id, teacher.id)


@router.post(
    "/{class_id}/roster/upload",
    summary="Upload class roster",
    description="Upload a CSV file containing the class roster with 'name' and 'email' columns.",
    responses={
        200: {"description": "Roster uploaded successfully"},
        400: {"description": "Invalid CSV file or format"},
        403: {"description": "Not the class owner"},
        404: {"description": "Class not found"},
    },
)
async def upload_class_roster(
    class_id: int,
    file: UploadFile = File(...),
    teacher: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db),
):
    """Upload a CSV roster for a specific class (teacher only)."""
    service = ClassService(db)
    return await service.upload_roster(class_id, teacher.id, file)
