import os
import math
import logging
from app.celery_app import celery_app
from app.config import settings
from app.audio import clean_audio
from app.llm import local_llm_correct, cloud_llm_correct, local_llm_extract, cloud_llm_extract, is_openai_configured
from app.heuristics import heuristic_correct, heuristic_extract
from pydub import AudioSegment

logger = logging.getLogger(__name__)

_whisper_model = None

def detect_gpu_device():
    """
    Automatically detects if GPU/CUDA is available for ctranslate2.
    Returns (device, compute_type) tuple.
    Uses 'float16' for GPU, and 'int8' for CPU to optimize performance and RAM.
    """
    try:
        import ctranslate2
        # Verify if compiled with CUDA and at least one device is visible
        if hasattr(ctranslate2, "get_supported_cuda_backends") and "cuda" in ctranslate2.get_supported_cuda_backends():
            if hasattr(ctranslate2, "get_cuda_device_count") and ctranslate2.get_cuda_device_count() > 0:
                logger.info("NVIDIA GPU/CUDA availability detected. Using GPU acceleration.")
                return "cuda", "float16"
    except Exception as e:
        logger.warning(f"Error during CUDA availability check: {e}")
        
    logger.info("CUDA not available. Defaulting to CPU with int8 quantization for speed.")
    return "cpu", "int8"

def get_whisper_model():
    """
    Initializes and returns the Faster-Whisper Model singleton.
    Standardizes on large-v3, falling back to medium and base.
    Persists models to the volume cache directory.
    """
    global _whisper_model
    if _whisper_model is None:
        from faster_whisper import WhisperModel
        
        # 1. Detect device and compute type
        device, compute_type = detect_gpu_device()
        
        # 2. Get configurations
        model_name = settings.WHISPER_MODEL or "large-v3"
        model_dir = os.getenv("WHISPER_MODEL_DIR", "/root/.cache/huggingface")
        
        logger.info(f"Loading Faster-Whisper model '{model_name}' on {device} ({compute_type}) using directory: {model_dir}")
        
        # Try loading preferred model (Offline first to prevent blocking HuggingFace API requests)
        try:
            logger.info(f"Attempting to load model '{model_name}' offline from cache...")
            _whisper_model = WhisperModel(
                model_name,
                device=device,
                compute_type=compute_type,
                download_root=model_dir,
                local_files_only=True
            )
            logger.info(f"Model '{model_name}' loaded successfully from local cache.")
        except Exception as local_err:
            logger.warning(f"Offline load failed: {local_err}. Retrying online load and download...")
            try:
                _whisper_model = WhisperModel(
                    model_name,
                    device=device,
                    compute_type=compute_type,
                    download_root=model_dir
                )
                logger.info(f"Model '{model_name}' loaded successfully (online).")
            except Exception as e:
                logger.error(f"Failed to load model '{model_name}' on {device} online: {e}. Retrying fallback chain...")
            
            # Fallback models sequentially
            fallbacks = ["medium", "base"] if model_name == "large-v3" else ["base"]
            for model_fb in fallbacks:
                try:
                    logger.info(f"Attempting to load fallback model '{model_fb}' on {device} ({compute_type})...")
                    _whisper_model = WhisperModel(
                        model_fb,
                        device=device,
                        compute_type=compute_type,
                        download_root=model_dir
                    )
                    logger.info(f"Fallback model '{model_fb}' loaded successfully.")
                    break
                except Exception as fb_err:
                    logger.error(f"Failed to load fallback model '{model_fb}': {fb_err}")
            
            # Absolute fallback to CPU and float32 if everything else failed
            if _whisper_model is None:
                logger.warning("All optimized CUDA/CPU loads failed. Falling back to CPU with float32.")
                for m in [model_name, "medium", "base"]:
                    try:
                        logger.info(f"Loading model '{m}' on CPU with float32...")
                        _whisper_model = WhisperModel(
                            m,
                            device="cpu",
                            compute_type="float32",
                            download_root=model_dir
                        )
                        logger.info(f"Model '{m}' loaded on CPU successfully.")
                        break
                    except Exception as cpu_err:
                        logger.error(f"CPU float32 loading failed for '{m}': {cpu_err}")
                        
        if _whisper_model is None:
            raise RuntimeError("Could not load any Faster-Whisper model.")
            
    return _whisper_model

@celery_app.task(bind=True, name="app.tasks.transcribe_task")
def transcribe_task(self, file_path: str):
    """
    Cleans audio (VAD, filters, noise gate), runs Whisper locally, and corrects vocabulary.
    """
    logger.info(f"Starting audio transcription task for: {file_path}")
    
    # 1. Update status to PREPARING_AUDIO
    self.update_state(state="PREPARING_AUDIO")
    
    # Clean and gate audio
    try:
        file_path = clean_audio(file_path)
    except Exception as clean_err:
        logger.error(f"Audio cleanup failed: {clean_err}")
        raise ValueError(f"Audio preparation error: {str(clean_err)}")
    
    # Read duration
    try:
        audio_seg = AudioSegment.from_file(file_path)
        audio_duration = len(audio_seg) / 1000.0
    except Exception as aud_err:
        audio_duration = 0.0
        logger.warning(f"Could not calculate audio duration: {aud_err}")

    # 2. Update status to TRANSCRIBING
    self.update_state(state="TRANSCRIBING")
    
    model = get_whisper_model()
    model_name = getattr(model, "model_path", settings.WHISPER_MODEL or "unknown")

    logger.info("==================================================")
    logger.info("Faster-Whisper Inference Engine:")
    logger.info(f"Active Model: {model_name}")
    logger.info(f"Audio Duration: {audio_duration:.2f} seconds")
    logger.info("==================================================")

    # Transcribe audio using Voice Activity Detection (VAD)
    try:
        segments_gen, info = model.transcribe(
            file_path,
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500)
        )
        segments = list(segments_gen)
    except Exception as vad_err:
        logger.warning(f"Transcription failed with VAD: {vad_err}. Retrying without VAD filter.")
        segments_gen, info = model.transcribe(
            file_path,
            beam_size=5,
            vad_filter=False
        )
        segments = list(segments_gen)

    transcript_text = ""
    detailed_segments = []
    total_prob = 0.0
    segment_count = 0
    
    for segment in segments:
        transcript_text += segment.text + " "
        prob = math.exp(segment.avg_logprob) if segment.avg_logprob is not None else 1.0
        prob = min(max(prob, 0.0), 1.0)
        
        detailed_segments.append({
            "start": round(segment.start, 2),
            "end": round(segment.end, 2),
            "text": segment.text.strip(),
            "confidence": round(prob, 2)
        })
        total_prob += prob
        segment_count += 1
        
    transcript_text = transcript_text.strip()
    avg_confidence = round(total_prob / segment_count, 2) if segment_count > 0 else 1.0
    
    # 3. Trading Vocabulary Correction Layer
    # Deterministic mapping of phonetic spelling errors and abbreviations
    corrected_transcript = heuristic_correct(transcript_text)
    logger.info(f"Heuristically corrected transcript: {corrected_transcript}")
    
    # Optionally refine corrected transcript using local LLM if configured
    try:
        refined = local_llm_correct(corrected_transcript)
        if refined and len(refined) > 2:
            corrected_transcript = refined
            logger.info(f"LLM refined transcript: {corrected_transcript}")
    except Exception as local_err:
        logger.warning(f"Local LLM refinement failed: {local_err}. Proceeding with vocabulary-corrected version.")
        # Fallback to cloud if configured and local failed
        if is_openai_configured():
            try:
                refined = cloud_llm_correct(corrected_transcript)
                if refined and len(refined) > 2:
                    corrected_transcript = refined
                    logger.info(f"Cloud LLM refined transcript: {corrected_transcript}")
            except Exception as cloud_err:
                logger.warning(f"Cloud LLM refinement failed: {cloud_err}")

    return {
        "original_transcript": transcript_text,
        "corrected_transcript": corrected_transcript,
        "whisper_confidence": avg_confidence,
        "detailed_segments": detailed_segments,
        "detected_language": info.language,
        "language_probability": round(info.language_probability, 2)
    }

@celery_app.task(name="app.tasks.extract_trade_task")
def extract_trade_task(transcript: str):
    """
    Extracts structured trade data from the corrected transcript.
    """
    logger.info("Starting structured trade extraction task.")
    is_fallback = False
    ai_data = None
    
    try:
        ai_data = local_llm_extract(transcript)
    except Exception as local_err:
        logger.warning(f"Local LLM extraction failed: {local_err}. Trying Cloud LLM.")
        if is_openai_configured():
            try:
                ai_data = cloud_llm_extract(transcript)
            except Exception as cloud_err:
                logger.warning(f"Cloud LLM extraction failed: {cloud_err}. Using heuristic fallback.")
                is_fallback = True
                ai_data = heuristic_extract(transcript)
        else:
            logger.info("Cloud LLM (OpenAI) not configured. Using heuristic fallback.")
            is_fallback = True
            ai_data = heuristic_extract(transcript)
            
    ai_data["is_fallback"] = is_fallback
    return ai_data

@celery_app.task(name="app.tasks.emotion_analysis_task")
def emotion_analysis_task(transcript: str):
    """
    Task to isolate emotion analysis.
    """
    logger.info("Starting emotion analysis task.")
    extracted = extract_trade_task(transcript)
    return {
        "emotions": extracted.get("emotions", []),
        "emotion_confidence": extracted.get("emotion_confidence", 0.0)
    }

@celery_app.task(name="app.tasks.generate_summary_task")
def generate_summary_task(transcript: str):
    """
    Task to isolate summary generation.
    """
    logger.info("Starting summary generation task.")
    extracted = extract_trade_task(transcript)
    return {
        "summary": extracted.get("summary", ""),
        "strengths": extracted.get("strengths", ""),
        "lessons_learned": extracted.get("lessons_learned", "")
    }
