from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2 import service_account
import os
import dotenv
from firebase_run import db, auth, verify_firebase_token
dotenv.load_dotenv()

SCOPES=["https://www.googleapis.com/auth/calendar.events.owned"]

def gcalendar_service():
    global calendar_id 
    calendar_id = os.getenv('COUNCILOG_CALENDAR_ID')
    creds = service_account.Credentials.from_service_account_file(
        os.getenv('COUNCILOG_SERVICE_ACCOUNT_FILE'), scopes=SCOPES)
    service = build('calendar', 'v3', credentials=creds)
    return service

def create_project(project_maker, project_name, project_description, assigned_members, 
                    tasks, priority, category, calendar_link, start_date, end_date):
    project = db.collection('projects').add({
        'project_maker': project_maker,
        'project_name': project_name,
        'project_description': project_description,
        'assigned_members': assigned_members,
        'tasks': tasks,
        'priority': priority,
        'category': category,
        'calendar_link': calendar_link,
        'start_date': start_date,
        'end_date': end_date
    })

def create_project(project_name, project_description, start_time, end_time):
    service = gcalendar_service()
    event = {
        'summary': project_name,
        'description': project_description,
        'start': {
            'dateTime': start_time,
            'timeZone': 'UTC',
        },
        'end': {
            'dateTime': end_time,
            'timeZone': 'UTC',
        },
    }
    try:
        event = service.events().insert(calendarId=calendar_id, body=event).execute()
        print('Event created: %s' % (event.get('htmlLink')))
    except HttpError as error:
        print('An error occurred: %s' % error)