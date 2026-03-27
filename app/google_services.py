from random import random
from flask import jsonify
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2 import service_account
from datetime import datetime, timedelta
import os
import dotenv
from app.session_id_generation import generate_secure_string
from .firebase_run import db, auth, verify_firebase_token
dotenv.load_dotenv()

SCOPES=["https://www.googleapis.com/auth/calendar.events.owned"]

def gcalendar_service():
    global calendar_id 
    calendar_id = os.getenv('COUNCILOG_CALENDAR_ID')
    creds = service_account.Credentials.from_service_account_file(
        os.getenv('COUNCILOG_SERVICE_ACCOUNT_FILE'), scopes=SCOPES)
    service = build('calendar', 'v3', credentials=creds)
    return service

def create_project_firestore(project_maker, project_name, project_description, assigned_members, 
                    tasks, status, priority, category, calendar_link, start_date, end_date):
    project = db.collection('projects').add({
        'project_uid': generate_secure_string(32),
        'project_maker': project_maker['name'],
        'project_maker_uid': project_maker['uid'],
        'project_name': project_name,
        'project_description': project_description,
        'assigned_members': assigned_members,
        'tasks': tasks,
        'status': status, 
        'priority': priority,
        'category': category,
        'calendar_link': calendar_link,
        'start_date': datetime.strptime(start_date, '%Y-%m-%d').isoformat(),
        'end_date': datetime.strptime(end_date, '%Y-%m-%d').isoformat()
    })
    
    return jsonify({
        'success': True,
        'project_id': project[1].id
    })

def create_project_gcalendar(project_name, project_description, start_time, end_time):
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
        
    return event.get('htmlLink')


def get_users():
    users = []
    try:
        users_ref = db.collection('users')
        docs = users_ref.stream()
        for doc in docs:
            user_data = doc.to_dict()
            users.append({
                'uid': user_data['uid'],
                'name': user_data['username']
            })
    except Exception as e:
        print(f"An error occurred while fetching users: {e}")
    
    return users

def get_projects_for_user(user_uid):
    projects = []
    try:
        projects_ref = db.collection('projects')
        docs = projects_ref.stream()
        for doc in docs:
            project_data = doc.to_dict()
            if user_uid in project_data.get('assigned_members', []):
                projects.append({
                    'project_uid': project_data.get('project_uid', ''),
                    'project_name': project_data.get('project_name', ''),
                    'project_description': project_data.get('project_description', ''),
                    'assigned_members': project_data.get('assigned_members', []),
                    'tasks': project_data.get('tasks', []),
                    'priority': project_data.get('priority', ''),
                    'status': project_data.get('status', ''),
                    'category': project_data.get('category', ''),
                    'calendar_link': project_data.get('calendar_link', ''),
                    'start_date': project_data.get('start_date', ''),
                    'end_date': project_data.get('end_date', '')
                })
    except Exception as e:
        print(f"An error occurred while fetching projects: {e}")
        projects = []
    return projects

def get_tasks_for_project_user(project_uid, user_uid):
    tasks = []
    try:
        projects_ref = db.collection('projects')
        docs = projects_ref.stream()
        for doc in docs:
            project_data = doc.to_dict()
            if project_data.get('project_uid') == project_uid:
                for task in project_data.get('tasks', []):
                    if user_uid in task.get('members', []):
                        tasks.append({
                            'name': task.get('name', ''),
                            'priority': task.get('priority', ''),
                            'status': task.get('status', ''),
                            'members': task.get('members', [])
                        })
    except Exception as e:
        print(f"An error occurred while fetching tasks: {e}")
        tasks = []
    return tasks