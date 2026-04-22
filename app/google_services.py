from random import random
from flask import jsonify
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2 import service_account
from datetime import datetime, timedelta
import os
import dotenv
from app.session_id_generation import generate_secure_string
from .firebase_run import db, auth, verify_firebase_token
dotenv.load_dotenv()

CALENDAR_SCOPES = ["https://www.googleapis.com/auth/calendar.events.owned"]

def gcalendar_service():
    global calendar_id 
    calendar_id = os.getenv('COUNCILOG_CALENDAR_ID')
    creds = service_account.Credentials.from_service_account_file(
        os.getenv('COUNCILOG_SERVICE_ACCOUNT_FILE'), scopes=CALENDAR_SCOPES)
    service = build('calendar', 'v3', credentials=creds)
    return service

def create_project_firestore(project_maker, project_name, project_description, assigned_members, 
                    tasks, status, priority, category, calendar_link, start_date, end_date):
    normalized_tasks = []
    for task in tasks:
        normalized_task = dict(task)
        normalized_task.setdefault('files', [])
        normalized_tasks.append(normalized_task)

    project = db.collection('projects').add({
        'project_uid': generate_secure_string(32),
        'project_maker': project_maker['name'],
        'project_maker_uid': project_maker['uid'],
        'project_name': project_name,
        'project_description': project_description,
        'assigned_members': assigned_members,
        'tasks': normalized_tasks,
        'project_files': [],
        'status': status, 
        'priority': priority,
        'category': category,
        'calendar_link': calendar_link,
        'start_date': start_date,
        'end_date': end_date
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


def create_task_gcalendar(task_name, project_name, due_date, description=""):
    """
    Create a Google Calendar event for a task.
    Uses all-day events with an exclusive end date.
    """
    try:
        service = gcalendar_service()
        due_datetime = datetime.strptime(due_date, '%Y-%m-%d')
        end_datetime = due_datetime + timedelta(days=1)
        event = {
            'summary': f'{task_name} — {project_name}',
            'description': description or f'Task for project {project_name}',
            'start': {
                'date': due_date,
                'timeZone': 'UTC',
            },
            'end': {
                'date': end_datetime.strftime('%Y-%m-%d'),
                'timeZone': 'UTC',
            },
        }
        created_event = service.events().insert(calendarId=calendar_id, body=event).execute()
        return {
            'htmlLink': created_event.get('htmlLink'),
            'id': created_event.get('id')
        }
    except HttpError as error:
        print(f'Google Calendar API error: {error}')
        return None
    except ValueError as error:
        print(f'Date parsing error: {error}')
        return None
    except Exception as error:
        print(f'Unexpected error creating task calendar event: {error}')
        return None


def update_task_event_status(event_id, task_name, project_name, new_status):
    try:
        if not event_id:
            return False
        service = gcalendar_service()
        base_summary = f"{task_name} — {project_name}"
        new_summary = f"✅ {base_summary}" if new_status == 'done' else base_summary
        service.events().patch(
            calendarId=calendar_id,
            eventId=event_id,
            body={'summary': new_summary}
        ).execute()
        return True
    except HttpError as error:
        print(f'Google Calendar API error updating event: {error}')
        return False
    except Exception as error:
        print(f'Unexpected error updating task calendar event: {error}')
        return False


def get_project_by_uid(project_uid):
    try:
        projects_ref = db.collection('projects')
        docs = projects_ref.stream()
        for doc in docs:
            project_data = doc.to_dict()
            if project_data.get('project_uid') == project_uid:
                return doc.id, project_data
    except Exception as e:
        print(f'Error fetching project by uid: {e}')
    return None, None


def get_user_calendar_events(user_uid):
    events = []
    try:
        projects_ref = db.collection('projects')
        docs = projects_ref.stream()

        for doc in docs:
            project_data = doc.to_dict()
            if user_uid not in project_data.get('assigned_members', []):
                continue

            project_start = project_data.get('start_date')
            project_end = project_data.get('end_date')
            if project_start and project_end:
                events.append({
                    'id': project_data.get('project_uid'),
                    'type': 'project',
                    'title': project_data.get('project_name'),
                    'description': project_data.get('project_description'),
                    'start_date': project_start.split('T')[0] if 'T' in project_start else project_start,
                    'end_date': project_end.split('T')[0] if 'T' in project_end else project_end,
                    'link': project_data.get('calendar_link', ''),
                })

            for task in project_data.get('tasks', []):
                if user_uid not in task.get('members', []):
                    continue
                due_date = task.get('due_date') or project_end
                if not due_date:
                    continue
                events.append({
                    'id': f"{project_data.get('project_uid')}_{task.get('name')}",
                    'type': 'task',
                    'title': task.get('name'),
                    'project': project_data.get('project_name'),
                    'due_date': due_date.split('T')[0] if 'T' in due_date else due_date,
                    'status': task.get('status', ''),
                    'priority': task.get('priority', ''),
                    'link': task.get('event_link', ''),
                })

    except Exception as e:
        print(f'Error getting calendar events: {e}')
    return events


def get_users():
    users = []
    try:
        users_ref = db.collection('users')
        docs = users_ref.stream()
        for doc in docs:
            user_data = doc.to_dict()
            users.append({
                'uid': user_data.get('uid', ''),
                'name': user_data.get('username', '') or user_data.get('name', ''),
                'email': user_data.get('email', ''),
                'picture': user_data.get('picture', ''),
                'role': user_data.get('role', 'Member')
            })
    except Exception as e:
        print(f"An error occurred while fetching users: {e}")
    
    return users

def get_member_summaries():
    summaries = {}
    try:
        projects_ref = db.collection('projects')
        docs = projects_ref.stream()
        for doc in docs:
            project_data = doc.to_dict()
            assigned_members = project_data.get('assigned_members', [])
            tasks = project_data.get('tasks', [])

            for member_uid in assigned_members:
                summary = summaries.setdefault(member_uid, {
                    'projects_count': 0,
                    'tasks_count': 0,
                    'open_tasks_count': 0,
                    'completed_tasks_count': 0
                })
                summary['projects_count'] += 1

            for task in tasks:
                task_members = task.get('members', [])
                status = task.get('status', 'todo')
                for member_uid in task_members:
                    summary = summaries.setdefault(member_uid, {
                        'projects_count': 0,
                        'tasks_count': 0,
                        'open_tasks_count': 0,
                        'completed_tasks_count': 0
                    })
                    summary['tasks_count'] += 1
                    if status == 'done':
                        summary['completed_tasks_count'] += 1
                    else:
                        summary['open_tasks_count'] += 1
    except Exception as e:
        print(f"An error occurred while fetching member summaries: {e}")
    return summaries

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
                    'project_files': project_data.get('project_files', []),
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
                event_id = None
                old_status = None
                task_found = False

                # Find and update the task
                for task in tasks:
                    if task.get('name') == task_name and user_uid in task.get('members', []):
                        old_status = task.get('status')
                        task['status'] = new_status
                        event_id = task.get('event_id')
                        project_name = project_data.get('project_name', '')
                        task_found = True
                        break

                if not task_found:
                    return {'success': False, 'message': 'Task not found or user not authorized'}

                # Update the project document
                doc_ref = projects_ref.document(doc.id)
                doc_ref.update({'tasks': tasks})

                if event_id and old_status != new_status:
                    update_task_event_status(event_id, task_name, project_name, new_status)

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
                task_data.setdefault('files', [])
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


def link_drive_file_to_project_task(project_uid, file_data, user_uid, task_name=None):
    try:
        file_id = file_data.get('file_id')
        if not file_id:
            return {'success': False, 'message': 'Missing file id'}

        projects_ref = db.collection('projects')
        docs = projects_ref.stream()

        for doc in docs:
            project_data = doc.to_dict()
            if project_data.get('project_uid') != project_uid:
                continue

            assigned_members = project_data.get('assigned_members', [])
            if user_uid not in assigned_members:
                return {'success': False, 'message': 'User not authorized for this project'}

            file_reference = {
                'file_id': file_data.get('file_id', ''),
                'name': file_data.get('name', ''),
                'mime_type': file_data.get('mime_type', ''),
                'size': file_data.get('size', '0'),
                'web_view_link': file_data.get('web_view_link', ''),
                'web_content_link': file_data.get('web_content_link', ''),
                'modified_time': file_data.get('modified_time', ''),
                'linked_by': user_uid,
                'linked_at': datetime.utcnow().isoformat() + 'Z'
            }

            doc_ref = projects_ref.document(doc.id)
            if task_name:
                tasks = project_data.get('tasks', [])
                for task in tasks:
                    if task.get('name') != task_name:
                        continue

                    if user_uid not in task.get('members', []) and user_uid not in assigned_members:
                        return {'success': False, 'message': 'User not authorized for this task'}

                    task_files = task.setdefault('files', [])
                    if not any(existing.get('file_id') == file_id for existing in task_files):
                        task_files.append(file_reference)

                    doc_ref.update({'tasks': tasks})
                    return {'success': True, 'message': 'File linked to task successfully'}

                return {'success': False, 'message': 'Task not found'}

            project_files = project_data.get('project_files', [])
            if not any(existing.get('file_id') == file_id for existing in project_files):
                project_files.append(file_reference)
                doc_ref.update({'project_files': project_files})

            return {'success': True, 'message': 'File linked to project successfully'}

        return {'success': False, 'message': 'Project not found'}
    except Exception as error:
        print(f'Error linking file to project/task: {error}')
        return {'success': False, 'message': str(error)}


def get_project_file_references(project_uid, user_uid):
    try:
        projects_ref = db.collection('projects')
        docs = projects_ref.stream()

        for doc in docs:
            project_data = doc.to_dict()
            if project_data.get('project_uid') != project_uid:
                continue

            if user_uid not in project_data.get('assigned_members', []):
                return {'success': False, 'message': 'User not authorized for this project'}

            task_files = []
            for task in project_data.get('tasks', []):
                if user_uid in task.get('members', []) and task.get('files'):
                    task_files.append({
                        'task_name': task.get('name', ''),
                        'files': task.get('files', [])
                    })

            return {
                'success': True,
                'project_files': project_data.get('project_files', []),
                'task_files': task_files
            }

        return {'success': False, 'message': 'Project not found'}
    except Exception as error:
        print(f'Error fetching project file references: {error}')
        return {'success': False, 'message': str(error)}