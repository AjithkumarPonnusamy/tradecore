import os
import logging
from pydub import AudioSegment

logger = logging.getLogger(__name__)

def apply_noise_gate(audio: AudioSegment, threshold_db: float = -45.0, attenuation_db: float = 15.0) -> AudioSegment:
    """
    Applies a simple noise gate to the audio.
    Chunks of audio below the threshold_db are attenuated by attenuation_db.
    This effectively silences/quiets background hiss and hum between active speech.
    """
    chunk_size_ms = 20  # 20ms chunks
    gated_audio = AudioSegment.empty()
    
    # Process audio in chunks
    for i in range(0, len(audio), chunk_size_ms):
        chunk = audio[i:i+chunk_size_ms]
        if chunk.dBFS < threshold_db:
            gated_audio += chunk - attenuation_db
        else:
            gated_audio += chunk
            
    return gated_audio

def clean_audio(file_path: str) -> str:
    """
    Enhances audio quality and performs validations:
    1. Rejects silent, too quiet (<-50 dBFS) or too short (<1s) recordings.
    2. Performs noise reduction using high/low pass filters and noise gating.
    3. Normalizes amplitude to -20 dBFS.
    4. Trims leading/trailing silence.
    Overwrites the file with the cleaned version and returns the path.
    """
    try:
        audio = AudioSegment.from_file(file_path)
    except Exception as e:
        logger.error(f"Error decoding audio with pydub: {e}")
        raise ValueError("Could not decode audio file. Make sure it is a valid format and ffmpeg is installed.")

    # 1. Validation: Duration check (original audio before silence trimming)
    duration_sec = len(audio) / 1000.0
    if duration_sec < 1.0:
        raise ValueError("Audio recording is too short. Please speak for at least 1 second.")

    # 2. Validation: Silence check
    if audio.dBFS == float("-inf") or audio.dBFS < -50.0:
        raise ValueError("Audio recording is silent or too quiet. Please speak closer to the microphone.")

    # 3. Noise Reduction Filters (Part 3)
    # High-pass filter (100 Hz) to eliminate low-end mic hum/rumble
    # Low-pass filter (8000 Hz) to cut out high-frequency hiss/static
    filtered_audio = audio.high_pass_filter(100).low_pass_filter(8000)
    
    # Apply Noise Gate to further suppress background room noise in silent passages
    gated_audio = apply_noise_gate(filtered_audio, threshold_db=-45.0, attenuation_db=15.0)

    # 4. Trim leading/trailing silence (threshold -50 dBFS)
    silence_threshold = -50.0
    chunk_size = 10
    
    leading_trim = 0
    while leading_trim < len(gated_audio) and gated_audio[leading_trim:leading_trim+chunk_size].dBFS < silence_threshold:
        leading_trim += chunk_size
        
    trailing_trim = len(gated_audio)
    while trailing_trim > leading_trim and gated_audio[trailing_trim-chunk_size:trailing_trim].dBFS < silence_threshold:
        trailing_trim -= chunk_size

    if leading_trim >= trailing_trim or (trailing_trim - leading_trim) < 1000:
        raise ValueError("Audio recording contains only silence or is too short after silence trimming.")
        
    trimmed_audio = gated_audio[leading_trim:trailing_trim]

    # 5. Amplitude normalization to -20 dBFS
    target_dBFS = -20.0
    change_in_dBFS = target_dBFS - trimmed_audio.dBFS
    normalized_audio = trimmed_audio.apply_gain(change_in_dBFS)

    ext = os.path.splitext(file_path)[1].lower().replace(".", "")
    if not ext or ext not in ["wav", "mp3", "m4a", "webm", "ogg"]:
        ext = "wav"
        
    normalized_audio.export(file_path, format=ext)
    return file_path
