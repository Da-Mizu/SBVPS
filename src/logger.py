"""
Logging centralisé pour le projet SBVPS
"""
import logging
import logging.handlers
import sys
from pathlib import Path
from src.config import LOG_LEVEL, PROJECT_ROOT

# Créer le dossier logs
logs_dir = PROJECT_ROOT / "logs"
logs_dir.mkdir(exist_ok=True)

# Formatter
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def get_logger(name):
    """Retourne un logger configuré"""
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL)

    # Handler Console avec UTF-8
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    # Force UTF-8 encoding
    if hasattr(console_handler, 'stream') and hasattr(console_handler.stream, 'reconfigure'):
        console_handler.stream.reconfigure(encoding='utf-8')
    logger.addHandler(console_handler)

    # Handler Fichier
    log_file = logs_dir / "sbvps.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=10485760, backupCount=5, encoding='utf-8'  # 10MB par fichier
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
