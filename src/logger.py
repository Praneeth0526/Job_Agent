# src/logger.py
import logging
import os
import sys

# --- Configuration ---
LOG_FILE = "data/agent.log"
LOG_LEVEL = logging.INFO


def setup_logger():
    """
    Sets up a centralized logger for the application.

    This logger will output to both a file and the console.
    It should be called only once when the application starts.
    """
    # Get the root logger
    logger = logging.getLogger()
    logger.setLevel(LOG_LEVEL)

    # Prevent adding multiple handlers if this function is called more than once
    if logger.hasHandlers():
        return logger

    # --- Create File Handler ---
    # This handler writes log messages to 'data/agent.log'
    try:
        # Ensure the log directory exists before creating the file handler
        log_dir = os.path.dirname(LOG_FILE)
        os.makedirs(log_dir, exist_ok=True)

        file_handler = logging.FileHandler(LOG_FILE, mode='a')  # 'a' for append
        file_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(module)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Error: Could not configure file logger. {e}", file=sys.stderr)

    # --- Create Console Handler ---
    # This handler prints log messages to the standard console
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    return logger
