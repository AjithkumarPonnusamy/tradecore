import os
import sys
from faster_whisper import WhisperModel

def download():
    model_name = "large-v3"
    model_dir = os.getenv("WHISPER_MODEL_DIR", "/root/.cache/huggingface")
    print(f"Starting synchronous model download for '{model_name}' to '{model_dir}'...")
    
    try:
        # This will download the model cleanly, resuming if possible, and verify it.
        model = WhisperModel(
            model_name,
            device="cpu",
            compute_type="int8",
            download_root=model_dir
        )
        print("Model downloaded and verified successfully!")
        sys.exit(0)
    except Exception as e:
        print(f"Error during model download: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    download()
