from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.models import User, SystemSetting, AuditLog, TaskExecutionLog, SchemaMigration
from app.schemas.schemas import (
    SystemSettingResponse, AuditLogResponse, TaskExecutionLogResponse
)

router = APIRouter(prefix="/system", tags=["System Schema"])

@router.get("/settings", response_model=List[SystemSettingResponse])
def get_system_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve global system settings."""
    return db.query(SystemSetting).all()


@router.get("/audit-logs", response_model=List[AuditLogResponse])
def get_audit_logs(
    action: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve security and action audit trail logs for the current user."""
    query = db.query(AuditLog).filter(AuditLog.user_id == current_user.id)
    if action:
        query = query.filter(AuditLog.action == action)
    return query.order_by(AuditLog.created_at.desc()).limit(limit).all()


@router.get("/tasks", response_model=List[TaskExecutionLogResponse])
def get_task_execution_logs(
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve background job execution timing and status logs."""
    return db.query(TaskExecutionLog).order_by(TaskExecutionLog.created_at.desc()).limit(limit).all()


@router.get("/migrations")
def get_schema_migrations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get applied database migration versions."""
    migrations = db.query(SchemaMigration).order_by(SchemaMigration.applied_at.desc()).all()
    return [{"version": m.version, "description": m.description, "applied_at": m.applied_at} for m in migrations]
