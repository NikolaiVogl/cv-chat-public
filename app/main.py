from fastapi import FastAPI, Request, APIRouter, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
from pydantic import BaseModel, validator
from typing import Optional
from app.config import settings
from app.services import load_resume
from app.llm import get_secure_llm_response
from app.calendar_service import find_available_slots, create_interview_event
from app.security import detect_prompt_injection, validate_email, validate_name, validate_duration, sanitize_input, MAX_QUESTION_LENGTH
from app.session import session_manager

# Setup Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

# Application state
app_state = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load resume on startup
    logger.info("Loading resume...")
    app_state["resume_text"] = load_resume() # Changed this line
    logger.info("Resume loaded successfully.")
    yield
    # Clean up on shutdown
    app_state.clear()
    logger.info("Application shutdown.")

# FastAPI App
app = FastAPI(lifespan=lifespan)

# Serve static files
app.mount("/static", StaticFiles(directory="app/static", html=True), name="static")

@app.get("/")
async def serve_index():
    return FileResponse("app/static/index.html")

# --- Q&A Router ---
qa_router = APIRouter()

class AskRequest(BaseModel):
    question: str
    session_id: Optional[str] = None
    
    @validator('question')
    def validate_question(cls, v):
        if not v or not v.strip():
            raise ValueError('Question cannot be empty')
        if len(v) > MAX_QUESTION_LENGTH:
            raise ValueError(f'Question too long (max {MAX_QUESTION_LENGTH} characters)')
        return v.strip()

@qa_router.post("/create-session")
async def create_session():
    """Create a new conversation session."""
    session_id = session_manager.create_session()
    return {"session_id": session_id}

@qa_router.post("/ask")
async def ask(payload: AskRequest):
    if not payload.question:
        raise HTTPException(status_code=400, detail="No question provided.")

    logger.info(f"Received question: {payload.question[:100]}...")  # Log only first 100 chars
    
    # Security check for prompt injection
    security_result = detect_prompt_injection(payload.question)
    
    if not security_result.is_safe:
        logger.warning(
            f"Blocked potentially unsafe question. Risk score: {security_result.risk_score}, "
            f"Patterns: {security_result.detected_patterns}"
        )
        raise HTTPException(
            status_code=400, 
            detail="Your question contains potentially unsafe content. Please rephrase your question about the resume."
        )
    
    # Use the cleaned input
    cleaned_question = security_result.cleaned_input
    
    # Get or create session
    session_id = payload.session_id
    session = None
    if session_id:
        session = session_manager.get_session(session_id) 
        if session:
            # Add user message to session
            session_manager.add_message(session_id, "user", cleaned_question)
    
    # Get resume content
    resume_text = app_state.get('resume_text', 'Resume not available.')
    
    # Use secure LLM response with session context
    return StreamingResponse(
        get_secure_llm_response(cleaned_question, resume_text, session), 
        media_type="text/plain",
        headers={"X-Session-ID": session_id or ""}
    )

# --- Scheduling Router ---
scheduling_router = APIRouter()

@scheduling_router.get("/get-availability")
async def get_availability():
    try:
        slots = find_available_slots()
        return {"slots": slots}
    except Exception as e:
        logger.exception("Error getting availability")
        raise HTTPException(status_code=500, detail=str(e))

class BookRequest(BaseModel):
    name: str
    email: str
    time: str
    duration_hours: float
    
    @validator('name')
    def validate_name_input(cls, v):
        if not v or not v.strip():
            raise ValueError('Name cannot be empty')
        cleaned_name = sanitize_input(v.strip(), 100)
        if not validate_name(cleaned_name):
            raise ValueError('Invalid name format')
        return cleaned_name
    
    @validator('email')
    def validate_email_input(cls, v):
        if not v or not v.strip():
            raise ValueError('Email cannot be empty')
        cleaned_email = sanitize_input(v.strip().lower(), 254)
        if not validate_email(cleaned_email):
            raise ValueError('Invalid email format')
        return cleaned_email
    
    @validator('time')
    def validate_time_input(cls, v):
        if not v or not v.strip():
            raise ValueError('Time cannot be empty')
        return sanitize_input(v.strip(), 50)
    
    @validator('duration_hours')
    def validate_duration_input(cls, v):
        if v is None:
            raise ValueError('Duration cannot be empty')
        # Duration should already be validated by frontend, but double-check
        if not isinstance(v, (int, float)) or v <= 0 or v > 8:
            raise ValueError('Invalid duration: must be between 0.25 and 8 hours')
        return float(v)

@scheduling_router.post("/book-interview")
async def book_interview(payload: BookRequest):
    try:
        # Additional logging for security monitoring
        logger.info(f"Interview booking attempt for {payload.email}")
        
        event = create_interview_event(payload.time, payload.email, payload.name, payload.duration_hours)
        return {"status": "success", "event_link": event.get('htmlLink')}
    except Exception as e:
        logger.exception("Error booking interview")
        raise HTTPException(status_code=500, detail=str(e))

app.include_router(qa_router, prefix="/qa")
app.include_router(scheduling_router, prefix="/scheduling")
