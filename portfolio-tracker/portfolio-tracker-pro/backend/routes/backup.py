"""
Backup API endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from backup_service import BackupService
from auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/backup", tags=["Backup"])

# Initialize backup service
backup_service = BackupService()


class BackupCreateRequest(BaseModel):
    description: Optional[str] = None
    include_sensitive: bool = False


class BackupRestoreRequest(BaseModel):
    backup_id: str
    overwrite: bool = False


class BackupDeleteRequest(BaseModel):
    backup_id: str


@router.post("/create", response_model=Dict[str, Any])
async def create_backup(
    request: BackupCreateRequest = None,
    current_user: Dict = Depends(get_current_user)
):
    """
    Create a new backup of all user data
    
    Args:
        request: Backup creation request (optional description, include_sensitive flag)
        current_user: Current authenticated user
        
    Returns:
        Backup metadata
    """
    try:
        description = request.description if request else None
        include_sensitive = request.include_sensitive if request else False
        
        # Create backup service with appropriate settings
        service = BackupService(include_sensitive=include_sensitive)
        result = service.create_backup(description=description)
        
        if not result.get('success'):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get('error', 'Failed to create backup')
            )
        
        return result
    except Exception as e:
        logger.error(f"Error creating backup: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating backup: {str(e)}"
        )


@router.get("/list", response_model=List[Dict[str, Any]])
async def list_backups(
    limit: int = 50,
    current_user: Dict = Depends(get_current_user)
):
    """
    List all available backups
    
    Args:
        limit: Maximum number of backups to return (default: 50)
        current_user: Current authenticated user
        
    Returns:
        List of backup metadata
    """
    try:
        backups = backup_service.list_backups(limit=limit)
        return backups
    except Exception as e:
        logger.error(f"Error listing backups: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing backups: {str(e)}"
        )


@router.get("/info/{backup_id}", response_model=Dict[str, Any])
async def get_backup_info(
    backup_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Get detailed information about a specific backup
    
    Args:
        backup_id: ID of the backup (format: YYYYMMDD_HHMMSS)
        current_user: Current authenticated user
        
    Returns:
        Backup details
    """
    try:
        info = backup_service.get_backup_info(backup_id)
        
        if info is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Backup {backup_id} not found"
            )
        
        return info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting backup info: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting backup info: {str(e)}"
        )


@router.post("/restore", response_model=Dict[str, Any])
async def restore_backup(
    request: BackupRestoreRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Restore data from a backup
    
    Args:
        request: Restore request (backup_id, overwrite flag)
        current_user: Current authenticated user
        
    Returns:
        Restore status
    """
    try:
        result = backup_service.restore_backup(
            backup_id=request.backup_id,
            overwrite=request.overwrite
        )
        
        if not result.get('success'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get('error', 'Failed to restore backup')
            )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error restoring backup: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error restoring backup: {str(e)}"
        )


@router.delete("/delete/{backup_id}", response_model=Dict[str, Any])
async def delete_backup(
    backup_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Delete a backup
    
    Args:
        backup_id: ID of the backup to delete
        current_user: Current authenticated user
        
    Returns:
        Delete status
    """
    try:
        result = backup_service.delete_backup(backup_id)
        
        if not result.get('success'):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.get('error', 'Failed to delete backup')
            )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting backup: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting backup: {str(e)}"
        )


@router.post("/cleanup", response_model=Dict[str, Any])
async def cleanup_old_backups(
    days: int = 30,
    keep_minimum: int = 5,
    current_user: Dict = Depends(get_current_user)
):
    """
    Delete old backups (keep minimum number)
    
    Args:
        days: Number of days to keep backups (default: 30)
        keep_minimum: Minimum number of backups to keep (default: 5)
        current_user: Current authenticated user
        
    Returns:
        Cleanup status
    """
    try:
        result = backup_service.delete_old_backups(days=days, keep_minimum=keep_minimum)
        return result
    except Exception as e:
        logger.error(f"Error cleaning up backups: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error cleaning up backups: {str(e)}"
        )



