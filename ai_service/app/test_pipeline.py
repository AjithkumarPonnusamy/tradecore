import sys
import logging
from app.tasks import detect_gpu_device
from app.heuristics import heuristic_correct, heuristic_extract

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("PipelineValidation")

def run_tests():
    logger.info("Starting AI voice journaling pipeline validation...")
    
    # Test 1: Device Detection
    logger.info("\n--- TEST 1: GPU / CUDA Detection ---")
    device, compute_type = detect_gpu_device()
    logger.info(f"Detected device: {device}")
    logger.info(f"Detected compute type: {compute_type}")
    
    # Test 2: Trading Vocabulary Correction
    logger.info("\n--- TEST 2: Trading Vocabulary Correction ---")
    test_cases = [
        ("I bought gold at two thousand three hundred fifty", "XAUUSD"),
        ("I want to check bank nifty for breakout", "BANKNIFTY"),
        ("the cpr range was wide today and vwap was flat", "CPR"),
        ("set sl at two thousand and target at three thousand", "Stop Loss"),
        ("price rejected from camarilla resistance and ema support", "Camarilla"),
        ("the risk reward ratio is one to two with tight trailing stop", "Risk Reward"),
        ("liquidation was hit early", "Liquidity")
    ]
    
    all_corrected_passed = True
    for input_text, expected_keyword in test_cases:
        corrected = heuristic_correct(input_text)
        passed = expected_keyword.lower() in corrected.lower()
        logger.info(f"Input: '{input_text}' -> Corrected: '{corrected}' | [{ 'PASSED' if passed else 'FAILED' }]")
        if not passed:
            all_corrected_passed = False
            
    # Test 3: Structured Heuristic Extraction
    logger.info("\n--- TEST 3: Heuristic Extraction ---")
    sample_transcript = (
        "I entered a buy trade on EURUSD at 1.0950. "
        "My stop loss was placed at 1.0900 and my target is 1.1050. "
        "The strategy used was a simple support bounce. "
        "I scaled out of the position when we hit resistance. "
        "I felt quite confident but exited early. No mistakes today."
    )
    
    logger.info(f"Sample transcript: '{sample_transcript}'")
    extracted = heuristic_extract(sample_transcript)
    
    expected_fields = {
        "symbol": "EURUSD",
        "direction": "BUY",
        "entry_price": 1.0950,
        "stop_loss": 1.0900,
        "target": 1.1050,
        "trade_management": "Partial Profit Booking",
        "strategy": "Support/Resistance Bounce"
    }
    
    all_extracted_passed = True
    for key, expected_val in expected_fields.items():
        actual_val = extracted.get(key)
        passed = actual_val == expected_val
        logger.info(f"Extracted Field '{key}': {actual_val} (Expected: {expected_val}) | [{ 'PASSED' if passed else 'FAILED' }]")
        if not passed:
            all_extracted_passed = False
            
    logger.info("\n==================================================")
    if all_corrected_passed and all_extracted_passed:
        logger.info("PIPELINE TEST SUCCESSFUL!")
        sys.exit(0)
    else:
        logger.error("PIPELINE TEST FAILED IN ONE OR MORE COMPONENTS.")
        sys.exit(1)

if __name__ == "__main__":
    run_tests()
