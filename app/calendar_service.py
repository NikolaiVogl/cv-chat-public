import datetime
import logging
import os
import json
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.config import settings

logger = logging.getLogger(__name__)

def get_credentials():
# Try individual environment variables for OAuth credentials
    client_id = os.getenv(settings.google_client_id_env)
    client_secret = os.getenv(settings.google_client_secret_env)
    refresh_token = os.getenv(settings.google_refresh_token_env)
    
    if client_id and client_secret and refresh_token:
        try:
            creds = Credentials(
                token=None,
                refresh_token=refresh_token,
                id_token=None,
                token_uri=settings.google_token_uri,
                client_id=client_id,
                client_secret=client_secret,
                scopes=settings.google_calendar_scopes
            )
            # Refresh the token if needed
            if not creds.valid:
                creds.refresh(Request())
            return creds
        except Exception as e:
            logger.error(f"Failed to create credentials from environment variables: {e}")
    
    logger.error(f"No valid Google Calendar credentials found in environment variables. "
                f"Please set "
                f"{settings.google_client_id_env}, {settings.google_client_secret_env}, "
                f"and {settings.google_refresh_token_env}.")
    return None

def find_available_slots():
    """
    Finds available 'interview block' slots in the calendar for the next 7 days.
    """
    creds = get_credentials()
    if not creds:
        return []
        
    try:
        service = build('calendar', 'v3', credentials=creds)
        now = datetime.datetime.utcnow().isoformat() + 'Z'
        time_max = (datetime.datetime.utcnow() + datetime.timedelta(days=settings.calendar_search_days)).isoformat() + 'Z'

        events_result = service.events().list(
            calendarId=settings.google_calendar_id,
            timeMin=now,
            timeMax=time_max,
            q=settings.interview_search_query,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        if not events:
            logger.info(f"No '{settings.interview_search_query}' events found in the next {settings.calendar_search_days} days.")
            return []

        return [event['start'].get('dateTime', event['start'].get('date')) for event in events]

    except HttpError as e:
        logger.error(f"An error occurred with Google Calendar API: {e}")
        return []

def create_interview_event(start_time_str, candidate_email, candidate_name, duration_hours=None):
    """
    Creates an interview event in the Google Calendar.
    """
    creds = get_credentials()
    if not creds:
        raise ConnectionError("Could not obtain Google API credentials.")

    service = build('calendar', 'v3', credentials=creds)
    
    start_time = datetime.datetime.fromisoformat(start_time_str)
    # Use custom duration if provided, otherwise use default from settings
    interview_duration = duration_hours if duration_hours is not None else settings.interview_duration_hours
    end_time = start_time + datetime.timedelta(hours=interview_duration)

    event = {
        'summary': f'Interview with {candidate_name}',
        'location': settings.interview_location,
        'description': f'Interview with candidate {candidate_name}.',
        'start': {'dateTime': start_time.isoformat(), 'timeZone': 'UTC'},
        'end': {'dateTime': end_time.isoformat(), 'timeZone': 'UTC'},
        'attendees': [
            {'email': candidate_email},
            {'email': settings.owner_email},
        ],
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'email', 'minutes': settings.interview_reminder_email_minutes},
                {'method': 'popup', 'minutes': settings.interview_reminder_popup_minutes},
            ],
        },
    }

    try:
        created_event = service.events().insert(calendarId=settings.google_calendar_id, body=event).execute()
        logger.info(f"Event created: {created_event.get('htmlLink')}")
        return created_event
    except HttpError as e:
        logger.error(f"Failed to create event: {e}")
        raise
