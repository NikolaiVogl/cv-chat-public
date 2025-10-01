from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    """
    Manages application settings and configurations.
    
    Settings are loaded exclusively from environment variables.
    """
    openai_api_key: str
    owner_email: str
    
    # The application directory, where this file is located
    app_dir: str = os.path.dirname(os.path.abspath(__file__))
    
    # Paths to resource files, now relative to the app directory
    resume_path: str = os.path.join(app_dir, "resume.txt")
    
    # Google Calendar API configuration
    google_calendar_scopes: list = ['https://www.googleapis.com/auth/calendar']
    google_service_account_info_env: str = 'GOOGLE_SERVICE_ACCOUNT_INFO'
    google_client_id_env: str = 'GOOGLE_CLIENT_ID'
    google_client_secret_env: str = 'GOOGLE_CLIENT_SECRET'
    google_refresh_token_env: str = 'GOOGLE_REFRESH_TOKEN'
    google_token_uri: str = "https://oauth2.googleapis.com/token"
    google_calendar_id: str = 'primary'
    interview_search_query: str = 'interview block'
    interview_location: str = 'Video Call'
    interview_reminder_email_minutes: int = 24 * 60  # 24 hours
    interview_reminder_popup_minutes: int = 10
    calendar_search_days: int = 7

    class Config:
        env_file = ".env"

settings = Settings()
