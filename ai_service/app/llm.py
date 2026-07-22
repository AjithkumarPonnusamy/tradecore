import requests
import json
import logging
from typing import Dict, Any
from app.config import settings

logger = logging.getLogger(__name__)

def is_openai_configured() -> bool:
    return bool(settings.OPENAI_API_KEY)

def cloud_llm_correct(transcript: str) -> str:
    """
    Fallback correction using OpenAI GPT API.
    """
    if not is_openai_configured():
        raise ValueError("OpenAI API Key is not configured.")

    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    system_prompt = (
        "You are an expert trading journal transcription editor. Your job is to clean up, correct spelling, "
        "and restore proper terminology (like 'XAUUSD', 'CPR', 'Camarilla', 'EMA', 'SL', 'Target', 'Forex', 'Nifty', etc.) "
        "in the user's trading journal transcript. Do not change the meaning of what the user said, "
        "simply fix transcription errors, capitalization of assets, punctuation, and grammar.\n\n"
        "Return ONLY the cleaned transcript without any explanations, notes, markdown, or code blocks."
    )

    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Raw Transcript: \"{transcript}\""}
        ],
        "temperature": 0.1
    }

    response = requests.post(url, headers=headers, json=payload, timeout=20)
    if response.status_code != 200:
        raise Exception(f"OpenAI GPT API error ({response.status_code}): {response.text}")

    res_data = response.json()
    content = res_data["choices"][0]["message"]["content"].strip()
    return clean_llm_markdown(content)

def cloud_llm_extract(transcript: str) -> Dict[str, Any]:
    """
    Fallback structured extraction using OpenAI GPT API.
    """
    if not is_openai_configured():
        raise ValueError("OpenAI API Key is not configured.")

    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    system_prompt = get_extraction_system_prompt()
    user_prompt = f"User Transcript: \"{transcript}\""

    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.2
    }

    response = requests.post(url, headers=headers, json=payload, timeout=40)
    if response.status_code != 200:
        raise Exception(f"OpenAI GPT API error ({response.status_code}): {response.text}")

    res_data = response.json()
    choice_text = res_data["choices"][0]["message"]["content"]
    
    try:
        return json.loads(choice_text)
    except Exception as e:
        raise Exception(f"Failed to parse OpenAI JSON response: {str(e)}. Response was: {choice_text}")

def local_llm_correct(transcript: str) -> str:
    """
    Calls local LLM API (Ollama) to correct trading terminology, spelling mistakes, grammar, and formatting in the transcript.
    """
    url = f"{settings.LLM_API_BASE.rstrip('/')}/chat/completions"
    
    system_prompt = (
        "You are an expert trading journal transcription editor. Your job is to clean up, correct spelling, "
        "and restore proper terminology (like 'XAUUSD', 'CPR', 'Camarilla', 'EMA', 'SL', 'Target', 'Forex', 'Nifty', etc.) "
        "in the user's trading journal transcript. Do not change the meaning of what the user said, "
        "simply fix transcription errors, capitalization of assets, punctuation, and grammar.\n\n"
        "Return ONLY the cleaned transcript without any explanations, notes, markdown, or code blocks."
    )

    payload = {
        "model": settings.LLM_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Raw Transcript: \"{transcript}\""}
        ],
        "temperature": 0.1
    }

    try:
        response = requests.post(url, json=payload, timeout=120)
        if response.status_code == 200:
            res_data = response.json()
            content = res_data["choices"][0]["message"]["content"].strip()
            return clean_llm_markdown(content)
        else:
            logger.warning(f"Local LLM correction API error ({response.status_code}): {response.text}")
    except Exception as e:
        logger.warning(f"Failed to communicate with Local LLM correction API: {e}")
        
    raise RuntimeError("Local LLM failed or offline. Proceeding to fallback cloud/heuristic correction.")

def local_llm_extract(transcript: str) -> Dict[str, Any]:
    """
    Calls local LLM API (Ollama/vLLM) to extract structured JSON metadata from the transcript.
    """
    url = f"{settings.LLM_API_BASE.rstrip('/')}/chat/completions"
    system_prompt = get_extraction_system_prompt()

    payload = {
        "model": settings.LLM_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"User Transcript: \"{transcript}\""}
        ],
        "temperature": 0.2
    }

    try:
        response = requests.post(url, json=payload, timeout=120)
        if response.status_code == 200:
            res_data = response.json()
            content = res_data["choices"][0]["message"]["content"].strip()
            content_cleaned = clean_llm_markdown(content)
            return json.loads(content_cleaned)
        else:
            logger.warning(f"Local LLM API error ({response.status_code}): {response.text}")
    except Exception as e:
        logger.warning(f"Failed to communicate with Local LLM API: {e}")
        
    raise RuntimeError("Local LLM failed or offline. Proceeding to fallback cloud/heuristic extraction.")

def clean_llm_markdown(content: str) -> str:
    cleaned = content.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    if cleaned.startswith('"') and cleaned.endswith('"'):
        cleaned = cleaned[1:-1].strip()
    return cleaned

def get_extraction_system_prompt() -> str:
    return (
        "You are a professional trading journal assistant. Analyze the user's trading voice journal transcript "
        "and extract structured metadata, key strengths, mistakes, lessons learned, emotional states, and generate a concise summary.\n\n"
        "Return a valid JSON object matching the following structure strictly. Do not add any extra comments, markdown formatting, or backticks:\n"
        "{\n"
        "  \"symbol\": \"string (uppercase asset symbol e.g. 'XAUUSD', 'NIFTY', 'BTCUSD', or null)\",\n"
        "  \"instrument\": \"string (uppercase asset symbol e.g. 'XAUUSD', 'NIFTY', 'BTCUSD', or null)\",\n"
        "  \"direction\": \"string ('BUY' or 'SELL', or null)\",\n"
        "  \"entry_price\": \"float or null\",\n"
        "  \"stop_loss\": \"float or null\",\n"
        "  \"target\": \"float or null\",\n"
        "  \"target_price\": \"float or null\",\n"
        "  \"exit_price\": \"float or null\",\n"
        "  \"strategy\": \"string (strategy name, or null)\",\n"
        "  \"setup\": \"string (technical chart setup, or null)\",\n"
        "  \"market\": \"string (usually 'Forex', 'Indian Market', 'Crypto', 'Commodity', or 'US Market', or null)\",\n"
        "  \"entry_reason\": \"string (why they entered, or null)\",\n"
        "  \"exit_reason\": \"string (why they exited, or null)\",\n"
        "  \"trade_management\": \"string (details about how the stop was moved, scaled out, or closed early, or null)\",\n"
        "  \"emotions\": \"array of strings (all identified emotions from this list: Fear, Greed, FOMO, Confidence, Patience, Revenge Trading, Hesitation, Discipline)\",\n"
        "  \"emotion_confidence\": \"float (confidence score from 0.0 to 1.0)\",\n"
        "  \"mistakes\": \"array of strings\",\n"
        "  \"lessons\": \"array of strings\",\n"
        "  \"summary\": \"string (short 1-2 sentence summary of the trade)\",\n"
        "  \"strengths\": \"string (what was done well, or null)\",\n"
        "  \"lessons_learned\": \"string (general trading lessons learned, or null)\"\n"
        "}"
    )
