import logging
from app.config import settings

logger = logging.getLogger(__name__)

def load_resume() -> str:
    """
    Loads resume text from the path specified in the settings.
    """
    try:
        with open(settings.resume_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"Resume file not found at path: {settings.resume_path}")
        return "Resume not available."
    except Exception as e:
        logger.error(f"Error loading resume: {e}")
        return "Error loading resume."
