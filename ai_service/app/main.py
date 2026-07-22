import os
import uuid
import time
import requests
import logging
from fastapi import FastAPI, Request, HTTPException, status, BackgroundTasks
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel
from celery.result import AsyncResult

from app.config import settings
from app.celery_app import celery_app
from app.tasks import transcribe_task, extract_trade_task, emotion_analysis_task, generate_summary_task, get_whisper_model

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s")
logger = logging.getLogger("tradecore_ai")

app = FastAPI(title="TradeCore AI Service", version="1.0.0")

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

app.add_middleware(RequestIDMiddleware)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    code_map = {
        status.HTTP_400_BAD_REQUEST: "BAD_REQUEST",
        status.HTTP_404_NOT_FOUND: "NOT_FOUND",
        status.HTTP_503_SERVICE_UNAVAILABLE: "SERVICE_UNAVAILABLE",
    }
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": code_map.get(exc.status_code, "HTTP_ERROR"),
            "message": exc.detail if isinstance(exc.detail, str) else "An HTTP error occurred.",
            "details": exc.detail if not isinstance(exc.detail, str) else None
        },
        headers=getattr(exc, "headers", None)
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "code": "VALIDATION_ERROR",
            "message": "Request payload validation failed.",
            "details": exc.errors()
        }
    )

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", "N/A")
    logger.error(f"[RequestID: {request_id}] Unhandled AI service exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "code": "INTERNAL_SERVER_ERROR",
            "message": "An internal server error occurred in AI service.",
            "details": None
        }
    )

class TranscribeRequest(BaseModel):
    file_path: str

class ExtractRequest(BaseModel):
    transcript: str

class EmotionRequest(BaseModel):
    transcript: str

class SummaryRequest(BaseModel):
    transcript: str

@app.post("/transcribe", status_code=status.HTTP_202_ACCEPTED)
def trigger_transcription(payload: TranscribeRequest):
    """
    Triggers asynchronous Whisper voice transcription.
    """
    if not os.path.exists(payload.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audio file not found at path: {payload.file_path}"
        )
        
    task = transcribe_task.delay(payload.file_path)
    return {"task_id": task.id, "status": task.status}

@app.post("/extract-trade", status_code=status.HTTP_202_ACCEPTED)
def trigger_trade_extraction(payload: ExtractRequest):
    """
    Triggers asynchronous structured trade parameters extraction.
    """
    task = extract_trade_task.delay(payload.transcript)
    return {"task_id": task.id, "status": task.status}

@app.post("/emotion-analysis", status_code=status.HTTP_202_ACCEPTED)
def trigger_emotion_analysis(payload: EmotionRequest):
    """
    Triggers asynchronous emotion profiling.
    """
    task = emotion_analysis_task.delay(payload.transcript)
    return {"task_id": task.id, "status": task.status}

@app.post("/generate-summary", status_code=status.HTTP_202_ACCEPTED)
def trigger_summary_generation(payload: SummaryRequest):
    """
    Triggers asynchronous summary generation.
    """
    task = generate_summary_task.delay(payload.transcript)
    return {"task_id": task.id, "status": task.status}

@app.get("/tasks/{task_id}")
def get_task_status(task_id: str):
    """
    Check the status and results of queued background tasks.
    """
    result = AsyncResult(task_id, app=celery_app)
    
    response = {
        "task_id": task_id,
        "status": result.status,
        "ready": result.ready()
    }
    
    if result.ready():
        if result.successful():
            response["result"] = result.result
        else:
            response["result"] = None
            response["error"] = str(result.result)
            
    return response

@app.get("/health")
def get_health():
    """
    Aggregates diagnostic stats for Ollama connection, Whisper loadability, and active Celery queues.
    """
    local_llm_reachable = False
    local_model_loaded = False
    loaded_models = []
    local_latency = None
    
    start_time = time.time()
    try:
        base_url = settings.LLM_API_BASE.replace("/v1", "")
        response = requests.get(f"{base_url}/api/tags", timeout=2)
        if response.status_code == 200:
            local_llm_reachable = True
            local_latency = round((time.time() - start_time) * 1000, 2)
            data = response.json()
            loaded_models = [m["name"] for m in data.get("models", [])]
            target_model = settings.LLM_MODEL
            if target_model in loaded_models or any(target_model in m for m in loaded_models):
                local_model_loaded = True
    except Exception:
        pass
        
    whisper_ready = False
    try:
        import app.tasks as tasks
        if tasks._whisper_model is not None:
            whisper_ready = True
    except Exception:
        pass
        
    celery_healthy = False
    try:
        inspect = celery_app.control.inspect()
        pings = inspect.ping()
        if pings:
            celery_healthy = True
    except Exception:
        pass
        
    return {
        "status": "Online",
        "whisper_ready": whisper_ready,
        "extraction_ready": local_llm_reachable,
        "queue_healthy": celery_healthy,
        "local_llm": {
            "reachable": local_llm_reachable,
            "model_loaded": local_model_loaded,
            "latency_ms": local_latency,
            "configured_model": settings.LLM_MODEL,
            "available_models": loaded_models
        },
        "cloud_llm": {
            "configured": bool(settings.OPENAI_API_KEY)
        }
    }

def pull_model_bg(model_name: str):
    try:
        base_url = settings.LLM_API_BASE.replace("/v1", "")
        requests.post(f"{base_url}/api/pull", json={"name": model_name}, timeout=300)
    except Exception as e:
        logger.error(f"Error pulling model {model_name} in background: {e}")

@app.post("/pull-model")
def pull_model_endpoint(background_tasks: BackgroundTasks):
    """
    Triggers pulling the configured model inside Ollama container in the background.
    """
    base_url = settings.LLM_API_BASE.replace("/v1", "")
    try:
        resp = requests.get(f"{base_url}/api/tags", timeout=2)
        if resp.status_code != 200:
            raise HTTPException(status_code=503, detail="Ollama endpoint offline.")
    except Exception:
        raise HTTPException(status_code=503, detail="Ollama endpoint offline.")
        
    background_tasks.add_task(pull_model_bg, settings.LLM_MODEL)
    return {"message": f"Started pulling model {settings.LLM_MODEL} in the background."}

