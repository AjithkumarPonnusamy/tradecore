import os
import time
import logging
import requests
from uuid import UUID
from celery.utils.log import get_task_logger

from app.core.celery_app import celery_app
from app.core.config import settings
from app.models.models import VoiceJournal

logger = get_task_logger(__name__)

def save_voice_journal_results(db, db_journal, ai_data, whisper_confidence, detailed_segments, detected_language, language_probability, is_fallback):
    ai_data["whisper_confidence"] = whisper_confidence
    ai_data["detailed_segments"] = detailed_segments
    ai_data["is_fallback"] = is_fallback
    ai_data["detected_language"] = detected_language
    ai_data["language_probability"] = language_probability
    
    # Extract emotions list for db tags
    emotions = ai_data.get("emotions", [])
    conf = ai_data.get("emotion_confidence", 1.0)
    formatted_emotions = [{"tag": emotion, "confidence": conf} for emotion in emotions]
    
    db_journal.ai_summary = ai_data
    db_journal.emotion_tags = formatted_emotions
    db_journal.status = "COMPLETED"
    db_journal.error_message = None
    
    db.commit()

@celery_app.task(name="app.tasks.voice.process_voice_journal_celery")
def process_voice_journal_celery(journal_id: str, file_path: str):
    """
    Background worker task to orchestrate voice journaling pipeline.
    It calls the AI service REST endpoints and polls Celery tasks,
    updating database states at each stage.
    """
    logger.info(f"Starting Celery background job for journal_id: {journal_id}")
    
    db = None
    try:
        from app.core.database import SessionLocal
        db = SessionLocal()
        
        db_journal = db.query(VoiceJournal).filter(VoiceJournal.id == UUID(journal_id)).first()
        if not db_journal:
            logger.error(f"Voice Journal record not found: {journal_id}")
            return
            
        # Step 1: Update status to PREPARING_AUDIO
        logger.info("Stage 1: Preparing Audio")
        db_journal.status = "PREPARING_AUDIO"
        db.commit()
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file not found: {file_path}")
            
        ai_service_url = settings.AI_SERVICE_URL.rstrip('/')
        
        # Step 2: Trigger transcription (which will clean/prepare, then transcribe)
        logger.info(f"Submitting transcription request to AI service for file: {file_path}")
        transcribe_resp = requests.post(
            f"{ai_service_url}/transcribe",
            json={"file_path": file_path},
            timeout=10
        )
        if transcribe_resp.status_code != 202:
            raise RuntimeError(f"AI Service transcription trigger failed: {transcribe_resp.text}")
            
        task_id = transcribe_resp.json()["task_id"]
        logger.info(f"AI Service transcription task triggered. Task ID: {task_id}")
        
        # Poll transcription task status
        transcript_data = None
        attempts = 0
        max_attempts = 120  # 4 minutes max for large models
        
        while attempts < max_attempts:
            time.sleep(1.5)
            attempts += 1
            status_resp = requests.get(f"{ai_service_url}/tasks/{task_id}", timeout=5)
            if status_resp.status_code == 200:
                res_json = status_resp.json()
                task_status = res_json.get("status", "")
                
                # Dynamic state sync based on AI task progression
                if task_status == "PREPARING_AUDIO" and db_journal.status != "PREPARING_AUDIO":
                    db_journal.status = "PREPARING_AUDIO"
                    db.commit()
                elif task_status == "TRANSCRIBING" and db_journal.status != "TRANSCRIBING":
                    db_journal.status = "TRANSCRIBING"
                    db.commit()
                
                if res_json["ready"]:
                    if res_json["status"] == "SUCCESS":
                        transcript_data = res_json["result"]
                        break
                    else:
                        error_detail = res_json.get("error", "Unknown AI service error")
                        # If validation error is present in the task result, raise it directly
                        raise ValueError(error_detail)
            else:
                logger.warning(f"Error polling AI Service task status ({status_resp.status_code}): {status_resp.text}")
                
        if not transcript_data:
            raise RuntimeError("AI Service transcription timed out.")
            
        transcript_text = transcript_data.get("original_transcript", "")
        corrected_transcript = transcript_data.get("corrected_transcript", "")
        avg_confidence = transcript_data.get("whisper_confidence", 1.0)
        detailed_segments = transcript_data.get("detailed_segments", [])
        detected_language = transcript_data.get("detected_language", "en")
        language_probability = transcript_data.get("language_probability", 1.0)
        
        logger.info(f"Transcription completed. Original: {transcript_text} | Corrected: {corrected_transcript}")
        
        # Save transcripts & set status to ANALYZING (for vocabulary correction and preparation)
        db_journal.original_transcript = transcript_text
        db_journal.corrected_transcript = corrected_transcript
        db_journal.transcript = corrected_transcript
        db_journal.status = "ANALYZING"
        db.commit()
        
        # Step 3: Trigger structured trade extraction
        logger.info("Stage 3: Extracting Trade Information")
        db_journal.status = "EXTRACTING"
        db.commit()
        
        extract_resp = requests.post(
            f"{ai_service_url}/extract-trade",
            json={"transcript": corrected_transcript},
            timeout=10
        )
        if extract_resp.status_code != 202:
            raise RuntimeError(f"AI Service extraction trigger failed: {extract_resp.text}")
            
        task_id = extract_resp.json()["task_id"]
        logger.info(f"AI Service extraction task triggered. Task ID: {task_id}")
        
        # Poll extraction task status
        ai_data = None
        attempts = 0
        while attempts < max_attempts:
            time.sleep(1.5)
            attempts += 1
            status_resp = requests.get(f"{ai_service_url}/tasks/{task_id}", timeout=5)
            if status_resp.status_code == 200:
                res_json = status_resp.json()
                if res_json["ready"]:
                    if res_json["status"] == "SUCCESS":
                        ai_data = res_json["result"]
                        break
                    else:
                        raise RuntimeError(f"AI Service extraction failed: {res_json.get('error')}")
            else:
                logger.warning(f"Error polling AI Service task status ({status_resp.status_code}): {status_resp.text}")
                
        if not ai_data:
            raise RuntimeError("AI Service extraction timed out.")
            
        # Step 4: Save results & mark COMPLETED
        save_voice_journal_results(
            db, db_journal, ai_data, 
            avg_confidence, detailed_segments, 
            detected_language, language_probability, 
            is_fallback=ai_data.get("is_fallback", False)
        )
        logger.info("Structured extraction populated successfully.")
        
    except ValueError as val_err:
        # These are validation errors like too silent or too short, show to the user
        logger.warning(f"Validation failure in voice processing: {val_err}")
        if db:
            try:
                db_journal = db.query(VoiceJournal).filter(VoiceJournal.id == UUID(journal_id)).first()
                if db_journal:
                    db_journal.status = "FAILED"
                    db_journal.error_message = str(val_err)
                    db.commit()
            except Exception as db_err:
                logger.error(f"Failed to record validation error in db: {db_err}")
                
    except Exception as e:
        # System errors (e.g. connection timeout, model loading error), show a generic friendly message
        logger.error(f"Unexpected error in Celery voice processing pipeline: {e}", exc_info=True)
        if db:
            try:
                db_journal = db.query(VoiceJournal).filter(VoiceJournal.id == UUID(journal_id)).first()
                if db_journal:
                    db_journal.status = "FAILED"
                    db_journal.error_message = (
                        "Unable to process your voice journal. Please make sure the audio is clear, "
                        "not silent, and try again."
                    )
                    db.commit()
            except Exception as db_err:
                logger.error(f"Failed to record pipeline error in db: {db_err}")
                
    finally:
        # Clean up files & url
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"Successfully deleted temporary audio file: {file_path}")
            except Exception as delete_err:
                logger.error(f"Failed to delete temporary audio file: {delete_err}")
        if db:
            try:
                db_journal = db.query(VoiceJournal).filter(VoiceJournal.id == UUID(journal_id)).first()
                if db_journal:
                    db_journal.audio_url = ""
                    db.commit()
            except Exception as db_err:
                logger.error(f"Failed to clear audio_url: {db_err}")
            db.close()
