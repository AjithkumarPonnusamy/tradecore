import os
import uuid
import shutil
import time
import requests
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc
from uuid import UUID
from typing import List, Dict, Any, Optional

from app.core.database import get_db
from app.core.config import settings
from app.api.auth import get_current_user
from app.models.models import User, VoiceJournal, Trade
from app.schemas.schemas import VoiceJournalResponse, VoiceJournalUpdate
from app.tasks.voice import process_voice_journal_celery

router = APIRouter(prefix="/voice-journal", tags=["Voice Journaling"])

# Local upload directory for audio files
LOCAL_UPLOAD_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "local_uploads"
)
os.makedirs(LOCAL_UPLOAD_DIR, exist_ok=True)

@router.post("/upload", response_model=VoiceJournalResponse, status_code=status.HTTP_202_ACCEPTED)
def upload_voice_journal(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Accepts browser recorded audio, saves locally, registers record with PROCESSING state,
    and runs transcription + extraction in background via Celery worker.
    """
    # Allowed formats
    allowed_extensions = {".mp3", ".wav", ".m4a", ".webm", ".ogg"}
    ext = os.path.splitext(file.filename)[1].lower()
    
    # In some recording APIs, filename is generic and might not have extension,
    # so we fallback to .webm if we can't detect it, or inspect content_type
    if not ext:
        if file.content_type == "audio/webm":
            ext = ".webm"
        elif file.content_type == "audio/wav" or file.content_type == "audio/wave":
            ext = ".wav"
        else:
            ext = ".webm"  # default standard

    filename = f"voice_{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(LOCAL_UPLOAD_DIR, filename)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as upload_err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save audio file locally: {str(upload_err)}"
        )

    # Audio URL relative path for serving via StaticFiles middleware
    audio_url = f"/static/uploads/{filename}"

    # Insert initial DB record
    db_journal = VoiceJournal(
        user_id=current_user.id,
        audio_url=audio_url,
        status="PROCESSING"
    )
    db.add(db_journal)
    db.commit()
    db.refresh(db_journal)

    # Spawn background Celery worker
    process_voice_journal_celery.delay(str(db_journal.id), file_path)

    return db_journal

@router.get("/status/{journal_id}", response_model=VoiceJournalResponse)
def get_voice_journal_status(
    journal_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Fetch the processing status and extraction results of a voice journal.
    """
    journal = db.query(VoiceJournal).filter(
        VoiceJournal.id == journal_id,
        VoiceJournal.user_id == current_user.id
    ).first()
    
    if not journal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Voice journal log not found."
        )
    return journal

@router.put("/{journal_id}/link/{trade_id}")
def link_voice_journal_to_trade(
    journal_id: UUID,
    trade_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Associate a completed voice journal with a saved trade log.
    """
    journal = db.query(VoiceJournal).filter(
        VoiceJournal.id == journal_id,
        VoiceJournal.user_id == current_user.id
    ).first()
    
    if not journal:
        raise HTTPException(status_code=404, detail="Voice journal not found.")

    trade = db.query(Trade).filter(
        Trade.id == trade_id,
        Trade.user_id == current_user.id
    ).first()
    
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found.")

    journal.trade_id = trade_id
    db.commit()
    return {"message": "Voice journal successfully linked to trade."}

@router.put("/{journal_id}", response_model=VoiceJournalResponse)
def update_voice_journal(
    journal_id: UUID,
    journal_in: VoiceJournalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update transcript, original/corrected transcript, and AI summary parameters of a voice journal.
    """
    journal = db.query(VoiceJournal).filter(
        VoiceJournal.id == journal_id,
        VoiceJournal.user_id == current_user.id
    ).first()
    
    if not journal:
        raise HTTPException(status_code=404, detail="Voice journal not found.")
        
    update_data = journal_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(journal, field, value)
        
    db.commit()
    db.refresh(journal)
    return journal

@router.get("/latest", response_model=List[VoiceJournalResponse])
def get_latest_voice_journals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Fetch latest voice journals recorded by the user.
    """
    return db.query(VoiceJournal).filter(
        VoiceJournal.user_id == current_user.id
    ).order_by(VoiceJournal.created_at.desc()).limit(10).all()

@router.delete("/{journal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_voice_journal(
    journal_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Deletes the voice journal record and removes the local audio file.
    """
    journal = db.query(VoiceJournal).filter(
        VoiceJournal.id == journal_id,
        VoiceJournal.user_id == current_user.id
    ).first()

    if not journal:
        raise HTTPException(status_code=404, detail="Voice journal not found.")

    # Remove physical file if it exists locally
    filename = os.path.basename(journal.audio_url)
    file_path = os.path.join(LOCAL_UPLOAD_DIR, filename)
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            print(f"Error removing physical audio file: {e}")

    db.delete(journal)
    db.commit()
    return None

@router.get("/ai-health")
def get_ai_health(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Check status metrics of the AI microservice (Whisper ready, Ollama ready, Celery healthy, latencies).
    """
    ai_service_online = False
    microservice_health = {}
    
    try:
        ai_service_url = settings.AI_SERVICE_URL.rstrip('/')
        response = requests.get(f"{ai_service_url}/health", timeout=3)
        if response.status_code == 200:
            ai_service_online = True
            microservice_health = response.json()
    except Exception:
        pass
        
    # Query last successful local/cloud inference (not a fallback)
    last_success_timestamp = None
    last_inference_status = "No runs yet"
    
    try:
        last_completed = db.query(VoiceJournal).filter(
            VoiceJournal.user_id == current_user.id,
            VoiceJournal.status == "COMPLETED"
        ).order_by(desc(VoiceJournal.created_at)).first()
        
        if last_completed:
            last_success_timestamp = (
                last_completed.updated_at.isoformat() 
                if last_completed.updated_at 
                else last_completed.created_at.isoformat()
            )
            if last_completed.error_message and "Advanced AI analysis is temporarily unavailable" in last_completed.error_message:
                last_inference_status = "Heuristic Fallback Used"
            else:
                last_inference_status = "Success (AI Extracted)"
    except Exception:
        pass

    # Extract properties from microservice health response
    local_llm = microservice_health.get("local_llm", {})
    cloud_llm = microservice_health.get("cloud_llm", {})
    
    return {
        "status": "Online" if ai_service_online else "Offline",
        "whisper_ready": microservice_health.get("whisper_ready", False),
        "extraction_ready": microservice_health.get("extraction_ready", False),
        "queue_healthy": microservice_health.get("queue_healthy", False),
        "local_llm": {
            "reachable": local_llm.get("reachable", False),
            "model_loaded": local_llm.get("model_loaded", False),
            "inference_working": local_llm.get("inference_working", False),
            "latency_ms": local_llm.get("latency_ms", None),
            "configured_model": local_llm.get("configured_model", settings.LLM_MODEL),
            "available_models": local_llm.get("available_models", [])
        },
        "cloud_llm": {
            "configured": cloud_llm.get("configured", False)
        },
        "monitoring": {
            "last_successful_inference": last_success_timestamp,
            "last_inference_status": last_inference_status
        }
    }

@router.post("/pull-model")
def pull_model(
    current_user: User = Depends(get_current_user)
):
    """
    Triggers pulling the configured model inside Ollama container in the background via AI service.
    """
    ai_service_url = settings.AI_SERVICE_URL.rstrip('/')
    try:
        resp = requests.post(f"{ai_service_url}/pull-model", timeout=5)
        if resp.status_code == 200:
            return resp.json()
        else:
            raise HTTPException(
                status_code=resp.status_code,
                detail=resp.json().get("detail", "Failed to pull model via AI service.")
            )
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI service connection error: {str(e)}"
        )
