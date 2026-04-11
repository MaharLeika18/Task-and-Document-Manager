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
    
    return {
        'success': True,
        'project_id': project[1].id
    }

def create_project_gcalendar(project_name, project_description, start_date, end_date):
    """
    Create a Google Calendar event for a project.
    For all-day events, the end date should be the next day since Google Calendar treats end date as exclusive.
    """
    try:
        service = gcalendar_service()

        # Validate dates
        start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
        end_datetime = datetime.strptime(end_date, '%Y-%m-%d')

        # For all-day events, add one day to end date (Google Calendar exclusive end date)
        end_datetime = end_datetime + timedelta(days=1)
        end_date_adjusted = end_datetime.strftime('%Y-%m-%d')

        event = {
            'summary': project_name,
            'description': project_description,
            'start': {
                'date': start_date,  # Use date for all-day events
                'timeZone': 'UTC',
            },
            'end': {
                'date': end_date_adjusted,  # Adjusted end date for all-day events
                'timeZone': 'UTC',
            },
        }

        created_event = service.events().insert(calendarId=calendar_id, body=event).execute()
        print(f'Event created successfully: {created_event.get("htmlLink")}')
        return created_event.get('htmlLink')

    except HttpError as error:
        print(f'Google Calendar API error: {error}')
        return None
    except ValueError as error:
        print(f'Date parsing error: {error}')
        return None
    except Exception as error:
        print(f'Unexpected error creating calendar event: {error}')
        return None


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

def update_task_status(project_uid, task_name, new_status, user_uid):
    """
    Update the status of a specific task in a project.
    Only allows updates if the user is assigned to the task.
    """
    try:
        projects_ref = db.collection('projects')
        docs = projects_ref.stream()

        for doc in docs:
            project_data = doc.to_dict()
            if project_data.get('project_uid') == project_uid:
                tasks = project_data.get('tasks', [])

                # Find and update the task
                for task in tasks:
                    if task.get('name') == task_name and user_uid in task.get('members', []):
                        task['status'] = new_status
                        break

                # Update the project document
                doc_ref = projects_ref.document(doc.id)
                doc_ref.update({'tasks': tasks})

                return {'success': True, 'message': 'Task status updated successfully'}

        return {'success': False, 'message': 'Project or task not found, or user not authorized'}

    except Exception as e:
        print(f"Error updating task status: {e}")
        return {'success': False, 'message': str(e)}

def add_task_to_project(project_uid, task_data, user_uid):
    """
    Add a new task to an existing project.
    Only project members can add tasks.
    """
    try:
        projects_ref = db.collection('projects')
        docs = projects_ref.stream()

        for doc in docs:
            project_data = doc.to_dict()
            if (project_data.get('project_uid') == project_uid and
                user_uid in project_data.get('assigned_members', [])):

                tasks = project_data.get('tasks', [])
                tasks.append(task_data)

                # Update the project document
                doc_ref = projects_ref.document(doc.id)
                doc_ref.update({'tasks': tasks})

                return {'success': True, 'message': 'Task added successfully'}

        return {'success': False, 'message': 'Project not found or user not authorized'}

    except Exception as e:
        print(f"Error adding task to project: {e}")
        return {'success': False, 'message': str(e)}

def get_tasks_for_project_user(project_uid, user_uid):
    """
    Get all tasks for a specific project that the user is assigned to.
    """
    try:
        projects_ref = db.collection('projects')
        docs = projects_ref.stream()

        for doc in docs:
            project_data = doc.to_dict()
            if (project_data.get('project_uid') == project_uid and
                user_uid in project_data.get('assigned_members', [])):

                tasks = project_data.get('tasks', [])
                # Filter tasks to only include those assigned to this user
                user_tasks = [task for task in tasks if user_uid in task.get('members', [])]
                return user_tasks

        return []

    except Exception as e:
        print(f"Error getting tasks: {e}")
        return []

def update_project_status(project_uid, new_status, user_uid):
    """
    Update the status of a project.
    Only project members can update status.
    """
    try:
        projects_ref = db.collection('projects')
        docs = projects_ref.stream()

        for doc in docs:
            project_data = doc.to_dict()
            if (project_data.get('project_uid') == project_uid and
                user_uid in project_data.get('assigned_members', [])):

                # Update the project document
                doc_ref = projects_ref.document(doc.id)
                doc_ref.update({'status': new_status})

                return {'success': True, 'message': 'Project status updated successfully'}

        return {'success': False, 'message': 'Project not found or user not authorized'}

    except Exception as e:
        print(f"Error updating project status: {e}")
        return {'success': False, 'message': str(e)}