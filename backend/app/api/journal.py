from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from datetime import datetime
from uuid import UUID
from typing import Dict, Any

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.models import User, TradeImage, Trade
from app.services.google_drive import drive_service

router = APIRouter(prefix="/journal", tags=["Journal Image Manager"])

@router.post("/upload-image")
def upload_journal_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload an image file directly to the user's connected Google Drive 'Trade Journal' folder.
    Fails if Google credentials are missing or expired (and cannot refresh).
    """
    if not current_user.google_access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google Drive is not connected. Please connect Google Drive in settings."
        )

    try:
        # Upload using the drive service
        upload_res = drive_service.upload_image(file, "journal", user_id=current_user.id, db=db)
        
        # Verify that it uploaded to Drive successfully (local ids start with 'local_')
        if upload_res["file_id"].startswith("local_"):
            raise Exception("Failed to upload file to Google Drive. Local fallback triggered.")
            
        return {
            "googleDriveFileId": upload_res["file_id"],
            "googleDriveFileUrl": upload_res["file_url"],
            "fileName": file.filename,
            "uploadedAt": datetime.utcnow().isoformat()
        }
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err)
        )
    except Exception as err:
        print(f"Error in upload_journal_image: {err}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(err)}"
        )

@router.delete("/image/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_journal_image(
    image_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete an image file from Google Drive and remove its DB reference.
    """
    image = db.query(TradeImage).join(Trade).filter(
        TradeImage.id == image_id,
        Trade.user_id == current_user.id
    ).first()
    
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found or access denied."
        )
        
    # Delete from Drive
    drive_service.delete_image(image.google_file_id, user_id=current_user.id, db=db)
    
    # Remove from Database
    db.delete(image)
    db.commit()
    return None

@router.put("/image/{image_id}")
def replace_journal_image(
    image_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Replace an existing image: deletes the old file on Google Drive and uploads a new one.
    """
    image = db.query(TradeImage).join(Trade).filter(
        TradeImage.id == image_id,
        Trade.user_id == current_user.id
    ).first()
    
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found or access denied."
        )

    try:
        # Delete old file from Google Drive
        drive_service.delete_image(image.google_file_id, user_id=current_user.id, db=db)
        
        # Upload new file
        upload_res = drive_service.upload_image(file, image.category, user_id=current_user.id, db=db)
        if upload_res["file_id"].startswith("local_"):
            raise Exception("Failed to upload new file to Google Drive. Fallback active.")
            
        # Update Database reference
        image.google_file_id = upload_res["file_id"]
        image.file_url = upload_res["file_url"]
        image.extra_data = {"filename": file.filename, "content_type": file.content_type}
        db.commit()
        db.refresh(image)
        
        return {
            "googleDriveFileId": image.google_file_id,
            "googleDriveFileUrl": image.file_url,
            "fileName": file.filename,
            "uploadedAt": datetime.utcnow().isoformat()
        }
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err)
        )
    except Exception as err:
        print(f"Error in replace_journal_image: {err}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Replacement failed: {str(err)}"
        )

@router.get("/image/{image_id}")
def get_journal_image(
    image_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get image metadata details.
    """
    image = db.query(TradeImage).join(Trade).filter(
        TradeImage.id == image_id,
        Trade.user_id == current_user.id
    ).first()
    
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found or access denied."
        )
        
    return {
        "id": image.id,
        "trade_id": image.trade_id,
        "category": image.category,
        "googleDriveFileId": image.google_file_id,
        "googleDriveFileUrl": image.file_url,
        "fileName": image.extra_data.get("filename") if image.extra_data else "markup.png",
        "caption": image.caption,
        "created_at": image.created_at
    }
