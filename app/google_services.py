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

# Status Constants
PROJECT_STATUSES = ['planning', 'active', 'on-hold', 'completed', 'cancelled']
TASK_STATUSES = ['todo', 'in-progress', 'in-review', 'done', 'blocked']

# Valid status transitions
VALID_PROJECT_TRANSITIONS = {
    'planning': ['active', 'cancelled'],
    'active': ['on-hold', 'completed', 'cancelled'],
    'on-hold': ['active', 'cancelled'],
    'completed': [],
    'cancelled': ['active']  # Can reopen if needed
}

VALID_TASK_TRANSITIONS = {
    'todo': ['in-progress', 'blocked'],
    'in-progress': ['in-review', 'done', 'blocked'],
    'in-review': ['done', 'in-progress', 'blocked'],
    'done': [],
    'blocked': ['todo', 'in-progress']
}

def normalize_task_status(status):
    if status == 'review':
        return 'in-review'
    return status

CALENDAR_SCOPES = ["https://www.googleapis.com/auth/calendar"]

_calendar_validated = False
_calendar_available = False

def gcalendar_service():
    global calendar_id 
    calendar_id = os.getenv('COUNCILOG_CALENDAR_ID')
    creds = service_account.Credentials.from_service_account_file(
        os.getenv('COUNCILOG_SERVICE_ACCOUNT_FILE'), scopes=CALENDAR_SCOPES)
    service = build('calendar', 'v3', credentials=creds)
    return service

def get_verified_calendar_id(service):
    global _calendar_validated
    global _calendar_available
    global calendar_id

    if _calendar_validated:
        return calendar_id if _calendar_available else None

    _calendar_validated = True
    if not calendar_id:
        _calendar_available = False
        return None

    try:
        service.calendars().get(calendarId=calendar_id).execute()
        _calendar_available = True
        return calendar_id
    except HttpError as error:
        print(f'Warning: Google Calendar ID not accessible: {error}')
        _calendar_available = False
        return None
    except Exception as error:
        print(f'Warning: Could not validate Google Calendar ID: {error}')
        _calendar_available = False
        return None

def create_project_firestore(project_maker, project_name, project_description, assigned_members, 
                    tasks, status, priority, category, calendar_link, calendar_event_id, start_date, end_date):
    from .google_drive_services import create_project_folder
    
    normalized_tasks = []
    for task in tasks:
        normalized_task = dict(task)
        normalized_task.setdefault('files', [])
        normalized_tasks.append(normalized_task)

    # Generate project UID first
    project_uid = generate_secure_string(32)
    
    # Create Google Drive folder for this project
    folder_result = create_project_folder(project_name, project_uid)
    drive_folder_id = None
    drive_folder_link = None
    
    if folder_result.get('success'):
        drive_folder_id = folder_result.get('folder_id')
        drive_folder_link = folder_result.get('web_view_link')
    else:
        print(f'Warning: Could not create Drive folder for project {project_name}: {folder_result.get("message")}')
    
    project = db.collection('projects').add({
        'project_uid': project_uid,
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
        'calendar_event_id': calendar_event_id,
        'start_date': start_date,
        'end_date': end_date,
        'drive_folder_id': drive_folder_id,
        'drive_folder_link': drive_folder_link
    })
    
    return {
        'success': True,
        'project_id': project[1].id,
        'project_uid': project_uid,
        'drive_folder_id': drive_folder_id
    }

def delete_project_calendar_event(project_data):
    try:
        service = gcalendar_service()
        verified_calendar_id = get_verified_calendar_id(service)
        if not verified_calendar_id:
            return False

        event_id = project_data.get('calendar_event_id')
        if event_id:
            service.events().delete(calendarId=verified_calendar_id, eventId=event_id).execute()
            return True

        calendar_link = project_data.get('calendar_link', '') or ''
        if not calendar_link:
            return False

        project_name = project_data.get('project_name', '')
        start_date = project_data.get('start_date', '')
        end_date = project_data.get('end_date', '')
        if not project_name or not start_date or not end_date:
            return False

        start_min = datetime.strptime(start_date, '%Y-%m-%d').isoformat() + 'Z'
        end_max = (datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=2)).isoformat() + 'Z'

        events_result = service.events().list(
            calendarId=verified_calendar_id,
            timeMin=start_min,
            timeMax=end_max,
            singleEvents=True,
            orderBy='startTime',
            q=project_name,
            fields='items(id,summary,start,end,description,htmlLink)'
        ).execute()

        for event in events_result.get('items', []):
            summary = event.get('summary', '')
            start = event.get('start', {})
            event_start = start.get('date', '') or start.get('dateTime', '').split('T')[0]
            if summary == project_name and event_start == start_date:
                service.events().delete(calendarId=verified_calendar_id, eventId=event.get('id')).execute()
                return True

        return False
    except Exception as error:
        print(f'Warning: failed to delete Google Calendar project event: {error}')
        return False

def create_project_gcalendar(project_name, project_description, start_date, end_date):
    """
    Create a Google Calendar event for a project.
    For all-day events, the end date should be the next day since Google Calendar treats end date as exclusive.
    """
    try:
        service = gcalendar_service()
        verified_calendar_id = get_verified_calendar_id(service)
        if not verified_calendar_id:
            return None

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

        created_event = service.events().insert(calendarId=verified_calendar_id, body=event).execute()
        print(f'Event created successfully: {created_event.get("htmlLink")}')
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
        print(f'Unexpected error creating calendar event: {error}')
        return None


def create_task_gcalendar(task_name, project_name, due_date, description=""):
    """
    Create a Google Calendar event for a task.
    Uses all-day events with an exclusive end date.
    """
    try:
        service = gcalendar_service()
        verified_calendar_id = get_verified_calendar_id(service)
        if not verified_calendar_id:
            return None
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
        created_event = service.events().insert(calendarId=verified_calendar_id, body=event).execute()
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
        verified_calendar_id = get_verified_calendar_id(service)
        if not verified_calendar_id:
            return False
        base_summary = f"{task_name} — {project_name}"
        new_summary = f"✅ {base_summary}" if new_status == 'done' else base_summary
        service.events().patch(
            calendarId=verified_calendar_id,
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


def update_task_event_details(event_id, task_name, project_name, due_date):
    try:
        if not event_id:
            return False
        if not due_date:
            return False

        service = gcalendar_service()
        verified_calendar_id = get_verified_calendar_id(service)
        if not verified_calendar_id:
            return False
        due_datetime = datetime.strptime(due_date, '%Y-%m-%d')
        end_datetime = due_datetime + timedelta(days=1)
        summary = f"{task_name} — {project_name}" if project_name else task_name

        service.events().patch(
            calendarId=verified_calendar_id,
            eventId=event_id,
            body={
                'summary': summary,
                'start': {
                    'date': due_date,
                    'timeZone': 'UTC',
                },
                'end': {
                    'date': end_datetime.strftime('%Y-%m-%d'),
                    'timeZone': 'UTC',
                }
            }
        ).execute()
        return True
    except HttpError as error:
        print(f'Google Calendar API error updating task details: {error}')
        return False
    except ValueError as error:
        print(f'Date parsing error updating task details: {error}')
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

            project_uid = project_data.get('project_uid')
            project_name = project_data.get('project_name')
            project_start = project_data.get('start_date')
            project_end = project_data.get('end_date')
            project_created = project_data.get('date_created') or project_start
            
            # Add project creation date event
            if project_created:
                created_date_str = project_created.split('T')[0] if 'T' in project_created else project_created
                events.append({
                    'id': f"{project_uid}_created",
                    'type': 'project_created',
                    'title': f"{project_name} (Created)",
                    'description': project_data.get('project_description'),
                    'created_date': created_date_str,
                    'event_date': created_date_str,
                    'link': project_data.get('calendar_link', ''),
                })
            
            # Add project start/end event
            if project_start and project_end:
                events.append({
                    'id': project_uid,
                    'type': 'project',
                    'title': project_name,
                    'description': project_data.get('project_description'),
                    'start_date': project_start.split('T')[0] if 'T' in project_start else project_start,
                    'end_date': project_end.split('T')[0] if 'T' in project_end else project_end,
                    'status': project_data.get('status', ''),
                    'priority': project_data.get('priority', ''),
                    'link': project_data.get('calendar_link', ''),
                })

            # Add task deadlines
            for task in project_data.get('tasks', []):
                if user_uid not in task.get('members', []):
                    continue
                due_date = task.get('due_date') or project_end
                if not due_date:
                    continue
                events.append({
                    'id': f"{project_uid}_{task.get('name')}",
                    'type': 'task',
                    'title': task.get('name'),
                    'project': project_name,
                    'due_date': due_date.split('T')[0] if 'T' in due_date else due_date,
                    'event_date': due_date.split('T')[0] if 'T' in due_date else due_date,
                    'status': task.get('status', ''),
                    'priority': task.get('priority', ''),
                    'members': task.get('members', []),
                    'link': task.get('event_link', ''),
                })

    except Exception as e:
        print(f'Error getting calendar events: {e}')
    return events


def get_google_calendar_events(user_uid):
    """Fetch events from Google Calendar for the user's calendar"""
    try:
        service = gcalendar_service()
        calendar_id = get_verified_calendar_id(service)
        
        if not calendar_id:
            return []
        
        # Fetch events from Google Calendar for the next 6 months
        now = datetime.utcnow().isoformat() + 'Z'
        six_months_later = (datetime.utcnow() + timedelta(days=180)).isoformat() + 'Z'
        
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=now,
            timeMax=six_months_later,
            singleEvents=True,
            orderBy='startTime',
            fields='items(id,summary,description,start,end,htmlLink,status)'
        ).execute()
        
        events = []
        for event in events_result.get('items', []):
            start = event.get('start', {})
            end = event.get('end', {})
            
            # Extract date from either dateTime or date field
            start_date = start.get('dateTime', start.get('date', '')).split('T')[0]
            end_date = end.get('dateTime', end.get('date', '')).split('T')[0]
            
            if start_date:
                events.append({
                    'id': event.get('id'),
                    'type': 'google_calendar',
                    'title': event.get('summary', 'Untitled'),
                    'description': event.get('description', ''),
                    'start_date': start_date,
                    'end_date': end_date,
                    'link': event.get('htmlLink', ''),
                    'status': event.get('status', 'confirmed'),
                    'source': 'google_calendar'
                })
        
        return events
    except Exception as e:
        print(f'Error fetching Google Calendar events: {e}')
        return []


def merge_calendar_events(user_uid):
    """Merge database events with Google Calendar events"""
    database_events = get_user_calendar_events(user_uid)
    google_events = get_google_calendar_events(user_uid)
    
    # Merge events, preferring database events for duplicates
    merged = {event['id']: event for event in google_events}
    for event in database_events:
        merged[event['id']] = event
    
    return list(merged.values())


def sync_task_to_google_calendar(task_event_id, task_name, project_name, status, due_date):
    """Sync task status changes to Google Calendar event description"""
    try:
        service = gcalendar_service()
        calendar_id = os.getenv('COUNCILOG_CALENDAR_ID')
        
        if not task_event_id or not calendar_id:
            return False
        
        # Get the current event
        event = service.events().get(
            calendarId=calendar_id,
            eventId=task_event_id
        ).execute()
        
        # Update description with status
        description = f"Task: {task_name}\nProject: {project_name}\nStatus: {status.replace('-', ' ').title()}\nUpdated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        event['description'] = description
        
        # Update the event
        service.events().update(
            calendarId=calendar_id,
            eventId=task_event_id,
            body=event
        ).execute()
        
        return True
    except HttpError as error:
        print(f'Error syncing task to Google Calendar: {error}')
        return False
    except Exception as e:
        print(f'Error syncing task to Google Calendar: {e}')
        return False


def get_users():
    users = []
    try:
        users_ref = db.collection('users')
        docs = users_ref.stream()
        for doc in docs:
            user_data = doc.to_dict()
            users.append({
                'uid': user_data.get('uid', ''),
                'name': user_data.get('display_name', '') or user_data.get('username', '') or user_data.get('name', '') or user_data.get('email', '').split('@')[0],
                'username': user_data.get('username', ''),
                'display_name': user_data.get('display_name', ''),
                'email': user_data.get('email', ''),
                'picture': user_data.get('picture', ''),
                'photo_source': user_data.get('photo_source', 'custom'),
                'role': user_data.get('role', 'Member')
            })
    except Exception as e:
        print(f"An error occurred while fetching users: {e}")
    
    return users


def get_user_profile(uid):
    try:
        user_doc = db.collection('users').document(uid).get()
        if not user_doc.exists:
            return {'success': False, 'message': 'User not found'}

        user_data = user_doc.to_dict()
        return {
            'success': True,
            'user': {
                'uid': user_data.get('uid', uid),
                'name': user_data.get('display_name', '') or user_data.get('username', '') or user_data.get('name', '') or user_data.get('email', '').split('@')[0],
                'username': user_data.get('username', ''),
                'display_name': user_data.get('display_name', ''),
                'email': user_data.get('email', ''),
                'picture': user_data.get('picture', ''),
                'photo_source': user_data.get('photo_source', 'custom'),
                'date_created': user_data.get('date_created', ''),
                'role': user_data.get('role', 'Member'),
            }
        }
    except Exception as e:
        print(f"An error occurred while fetching the user profile: {e}")
        return {'success': False, 'message': str(e)}


def update_user_profile(uid, display_name=None, picture=None, photo_source=None):
    try:
        user_ref = db.collection('users').document(uid)
        user_doc = user_ref.get()
        if not user_doc.exists:
            return {'success': False, 'message': 'User not found'}

        updates = {}
        if display_name is not None:
            updates['display_name'] = display_name.strip()
            updates['username'] = display_name.strip()
        if picture is not None:
            updates['picture'] = picture.strip()
        if photo_source is not None:
            updates['photo_source'] = photo_source

        if not updates:
            return {'success': False, 'message': 'No profile changes provided'}

        user_ref.update(updates)

        auth_updates = {}
        if display_name is not None:
            auth_updates['display_name'] = display_name.strip() or None
        if picture is not None and picture.strip():
            auth_updates['photo_url'] = picture.strip()

        if auth_updates:
            auth.update_user(uid, **auth_updates)

        profile_result = get_user_profile(uid)
        if profile_result.get('success'):
            return {
                'success': True,
                'user': profile_result.get('user')
            }

        return {'success': True, 'message': 'Profile updated successfully'}
    except Exception as e:
        print(f"An error occurred while updating the user profile: {e}")
        return {'success': False, 'message': str(e)}


def delete_user_account(uid):
    try:
        projects_ref = db.collection('projects')
        docs = projects_ref.stream()

        for doc in docs:
            project_data = doc.to_dict()
            changed = False

            assigned_members = project_data.get('assigned_members', [])
            if uid in assigned_members:
                assigned_members = [member_uid for member_uid in assigned_members if member_uid != uid]
                changed = True

            tasks = project_data.get('tasks', [])
            for task in tasks:
                task_members = task.get('members', [])
                if uid in task_members:
                    task['members'] = [member_uid for member_uid in task_members if member_uid != uid]
                    changed = True

            if changed:
                projects_ref.document(doc.id).update({
                    'assigned_members': assigned_members,
                    'tasks': tasks
                })

        db.collection('users').document(uid).delete()

        try:
            auth.delete_user(uid)
        except Exception as auth_error:
            print(f"Warning: Firebase Auth delete failed for {uid}: {auth_error}")

        return {'success': True, 'message': 'Account deleted successfully'}
    except Exception as e:
        print(f"An error occurred while deleting the user account: {e}")
        return {'success': False, 'message': str(e)}

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
                    'end_date': project_data.get('end_date', ''),
                    'drive_folder_id': project_data.get('drive_folder_id', ''),
                    'drive_folder_link': project_data.get('drive_folder_link', '')
                })
    except Exception as e:
        print(f"An error occurred while fetching projects: {e}")
        projects = []
    return projects

def update_task_status(project_uid, task_name, new_status, user_uid):
    """
    Update the status of a specific task in a project.
    Only allows updates if the user is assigned to the task.
    Validates status transitions and logs audit trail.
    """
    try:
        new_status = normalize_task_status(new_status)
        # Validate new status
        if new_status not in TASK_STATUSES:
            return {
                'success': False,
                'message': f'Invalid status. Valid statuses are: {" | ".join(TASK_STATUSES)}'
            }

        projects_ref = db.collection('projects')
        docs = projects_ref.stream()

        for doc in docs:
            project_data = doc.to_dict()
            if project_data.get('project_uid') == project_uid:
                tasks = project_data.get('tasks', [])
                event_id = None
                old_status = None
                task_found = False
                task_index = -1

                # Find and validate task and user authorization
                for idx, task in enumerate(tasks):
                    if task.get('name') == task_name and user_uid in task.get('members', []):
                        old_status = normalize_task_status(task.get('status', 'todo'))
                        
                        # Validate status transition
                        valid_transitions = VALID_TASK_TRANSITIONS.get(old_status, [])
                        if new_status not in valid_transitions:
                            return {
                                'success': False,
                                'message': f'Cannot transition from "{old_status}" to "{new_status}". Valid transitions: {" | ".join(valid_transitions) if valid_transitions else "No transitions available (terminal state)"}'  
                            }
                        
                        task['status'] = new_status
                        task['last_updated'] = datetime.now().isoformat()
                        task['last_updated_by'] = user_uid
                        
                        # Add to audit trail
                        if 'status_history' not in task:
                            task['status_history'] = []
                        task['status_history'].append({
                            'status': new_status,
                            'changed_by': user_uid,
                            'changed_at': datetime.now().isoformat(),
                            'previous_status': old_status
                        })
                        
                        event_id = task.get('event_id')
                        project_name = project_data.get('project_name', '')
                        task_found = True
                        task_index = idx
                        break

                if not task_found:
                    return {'success': False, 'message': 'Task not found or user not authorized'}

                # Update the project document
                doc_ref = projects_ref.document(doc.id)
                doc_ref.update({'tasks': tasks})

                if event_id and old_status != new_status:
                    update_task_event_status(event_id, task_name, project_name, new_status)

                return {
                    'success': True,
                    'message': f'Task status updated from "{old_status}" to "{new_status}"',
                    'old_status': old_status,
                    'new_status': new_status,
                    'task': tasks[task_index] if task_index >= 0 else None
                }

        return {'success': False, 'message': 'Project not found'}

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
    Validates status transitions and logs audit trail.
    """
    try:
        # Validate new status
        if new_status not in PROJECT_STATUSES:
            return {
                'success': False,
                'message': f'Invalid status. Valid statuses are: {" | ".join(PROJECT_STATUSES)}'
            }

        projects_ref = db.collection('projects')
        docs = projects_ref.stream()

        for doc in docs:
            project_data = doc.to_dict()
            if project_data.get('project_uid') == project_uid:
                # Check authorization
                if user_uid not in project_data.get('assigned_members', []):
                    return {'success': False, 'message': 'Not authorized to update project status'}
                
                old_status = project_data.get('status', 'planning')
                
                # Validate status transition
                valid_transitions = VALID_PROJECT_TRANSITIONS.get(old_status, [])
                if new_status not in valid_transitions:
                    return {
                        'success': False,
                        'message': f'Cannot transition from "{old_status}" to "{new_status}". Valid transitions: {" | ".join(valid_transitions) if valid_transitions else "No transitions available (terminal state)"}'
                    }
                
                # Prepare update data
                update_data = {
                    'status': new_status,
                    'last_updated': datetime.now().isoformat(),
                    'last_updated_by': user_uid
                }
                
                # Add to status history
                status_history = project_data.get('status_history', [])
                status_history.append({
                    'status': new_status,
                    'changed_by': user_uid,
                    'changed_at': datetime.now().isoformat(),
                    'previous_status': old_status
                })
                update_data['status_history'] = status_history

                # Update the project document
                doc_ref = projects_ref.document(doc.id)
                doc_ref.update(update_data)

                return {
                    'success': True,
                    'message': f'Project status updated from "{old_status}" to "{new_status}"',
                    'old_status': old_status,
                    'new_status': new_status
                }

        return {'success': False, 'message': 'Project not found'}

    except Exception as e:
        print(f"Error updating project status: {e}")
        return {'success': False, 'message': str(e)}


def update_project_details(project_uid, updated_data, user_uid):
    try:
        projects_ref = db.collection('projects')
        docs = projects_ref.stream()

        for doc in docs:
            project_data = doc.to_dict()
            if project_data.get('project_uid') != project_uid:
                continue

            if user_uid not in project_data.get('assigned_members', []):
                return {'success': False, 'message': 'Not authorized to update project details'}

            status_to_update = updated_data.get('status')
            if status_to_update and status_to_update != project_data.get('status'):
                status_result = update_project_status(project_uid, status_to_update, user_uid)
                if not status_result.get('success'):
                    return status_result

            update_data = {}
            for key in ['project_name', 'project_description', 'priority', 'category', 'start_date', 'end_date', 'assigned_members']:
                if updated_data.get(key) is not None:
                    update_data[key] = updated_data.get(key)

            if update_data:
                update_data['last_updated'] = datetime.now().isoformat()
                update_data['last_updated_by'] = user_uid
                projects_ref.document(doc.id).update(update_data)

            return {'success': True, 'message': 'Project details updated successfully'}

        return {'success': False, 'message': 'Project not found'}

    except Exception as e:
        print(f'Error updating project details: {e}')
        return {'success': False, 'message': str(e)}


def update_task_details(project_uid, task_name, task_updates, user_uid):
    try:
        projects_ref = db.collection('projects')
        docs = projects_ref.stream()

        for doc in docs:
            project_data = doc.to_dict()
            if project_data.get('project_uid') != project_uid:
                continue

            if user_uid not in project_data.get('assigned_members', []) and not any(user_uid in t.get('members', []) for t in project_data.get('tasks', [])):
                return {'success': False, 'message': 'Not authorized to update task details'}

            tasks = project_data.get('tasks', [])
            task_found = False
            for task in tasks:
                if task.get('name') == task_name:
                    task_found = True
                    if user_uid not in task.get('members', []) and user_uid not in project_data.get('assigned_members', []):
                        return {'success': False, 'message': 'Not authorized to update this task'}

                    new_name = task_updates.get('name')
                    new_priority = task_updates.get('priority')
                    new_due_date = task_updates.get('due_date')
                    new_members = task_updates.get('members')
                    new_status = normalize_task_status(task_updates.get('status'))

                    old_status = normalize_task_status(task.get('status', 'todo'))
                    if new_status and new_status != old_status:
                        valid_transitions = VALID_TASK_TRANSITIONS.get(old_status, [])
                        if new_status not in valid_transitions:
                            return {
                                'success': False,
                                'message': f'Cannot transition from "{old_status}" to "{new_status}". Valid transitions: {" | ".join(valid_transitions) if valid_transitions else "No transitions available (terminal state)"}'
                            }
                        task['status'] = new_status
                        if 'status_history' not in task:
                            task['status_history'] = []
                        task['status_history'].append({
                            'status': new_status,
                            'changed_by': user_uid,
                            'changed_at': datetime.now().isoformat(),
                            'previous_status': old_status
                        })
                        if task.get('event_id'):
                            update_task_event_status(task.get('event_id'), new_name or task.get('name'), project_data.get('project_name', ''), new_status)

                    if new_name and new_name != task.get('name'):
                        task['name'] = new_name

                    if new_priority is not None:
                        task['priority'] = new_priority

                    if new_due_date is not None:
                        task['due_date'] = new_due_date

                    if isinstance(new_members, list):
                        task['members'] = new_members
                        if user_uid not in task['members']:
                            task['members'].append(user_uid)

                    if task.get('event_id') and (new_name or new_due_date):
                        update_task_event_details(
                            task.get('event_id'),
                            new_name or task.get('name'),
                            project_data.get('project_name', ''),
                            new_due_date or task.get('due_date')
                        )

                    task['last_updated'] = datetime.now().isoformat()
                    task['last_updated_by'] = user_uid
                    break

            if not task_found:
                return {'success': False, 'message': 'Task not found'}

            doc_ref = projects_ref.document(doc.id)
            doc_ref.update({'tasks': tasks})
            return {'success': True, 'message': 'Task details updated successfully', 'task': task}

        return {'success': False, 'message': 'Project not found'}

    except Exception as e:
        print(f'Error updating task details: {e}')
        return {'success': False, 'message': str(e)}


def delete_project(project_uid, user_uid):
    try:
        projects_ref = db.collection('projects')
        docs = projects_ref.stream()

        for doc in docs:
            project_data = doc.to_dict()
            if project_data.get('project_uid') != project_uid:
                continue

            if user_uid not in project_data.get('assigned_members', []) and user_uid != project_data.get('project_maker_uid'):
                return {'success': False, 'message': 'Not authorized to delete this project'}

            delete_project_calendar_event(project_data)
            projects_ref.document(doc.id).delete()
            return {'success': True, 'message': 'Project deleted successfully'}

        return {'success': False, 'message': 'Project not found'}

    except Exception as e:
        print(f'Error deleting project: {e}')
        return {'success': False, 'message': str(e)}


def delete_task(project_uid, task_name, user_uid):
    try:
        projects_ref = db.collection('projects')
        docs = projects_ref.stream()

        for doc in docs:
            project_data = doc.to_dict()
            if project_data.get('project_uid') != project_uid:
                continue

            tasks = project_data.get('tasks', [])
            task_index = None
            for index, task in enumerate(tasks):
                if task.get('name') == task_name:
                    task_index = index
                    break

            if task_index is None:
                return {'success': False, 'message': 'Task not found'}

            task = tasks[task_index]
            if user_uid not in project_data.get('assigned_members', []) and user_uid not in task.get('members', []):
                return {'success': False, 'message': 'Not authorized to delete this task'}

            event_id = task.get('event_id')
            if event_id:
                try:
                    service = gcalendar_service()
                    service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
                except Exception as e:
                    print(f'Warning: failed to delete Google Calendar event for task {task_name}: {e}')

            tasks.pop(task_index)
            doc_ref = projects_ref.document(doc.id)
            doc_ref.update({'tasks': tasks})
            return {'success': True, 'message': 'Task deleted successfully'}

        return {'success': False, 'message': 'Project not found'}

    except Exception as e:
        print(f'Error deleting task: {e}')
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

            upsert_drive_file_record(file_reference)

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


def upsert_drive_file_record(file_data, project_uid=None, task_name=None, linked_by=None):
    try:
        file_id = file_data.get('file_id')
        if not file_id:
            return {'success': False, 'message': 'Missing file id'}

        record = {
            'file_id': file_id,
            'name': file_data.get('name', ''),
            'mime_type': file_data.get('mime_type', ''),
            'size': file_data.get('size', '0'),
            'modified_time': file_data.get('modified_time', ''),
            'web_view_link': file_data.get('web_view_link', ''),
            'web_content_link': file_data.get('web_content_link', ''),
            'icon_link': file_data.get('icon_link', ''),
            'parent_id': file_data.get('parent_id', ''),
            'project_uid': project_uid or file_data.get('project_uid', ''),
            'task_name': task_name or file_data.get('task_name', ''),
            'linked_by': linked_by or file_data.get('linked_by', ''),
            'updated_at': datetime.utcnow().isoformat() + 'Z',
        }

        db.collection('drive_files').document(file_id).set(record, merge=True)
        return {'success': True, 'record': record}
    except Exception as error:
        print(f'Error upserting drive file record: {error}')
        return {'success': False, 'message': str(error)}


def delete_drive_file_record(file_id):
    try:
        db.collection('drive_files').document(file_id).delete()
        return {'success': True}
    except Exception as error:
        print(f'Error deleting drive file record: {error}')
        return {'success': False, 'message': str(error)}


def remove_drive_file_references(file_id):
    try:
        projects_ref = db.collection('projects')
        docs = projects_ref.stream()

        for doc in docs:
            project_data = doc.to_dict()
            changed = False

            project_files = [file_ref for file_ref in project_data.get('project_files', []) if file_ref.get('file_id') != file_id]
            if len(project_files) != len(project_data.get('project_files', [])):
                changed = True

            tasks = project_data.get('tasks', [])
            for task in tasks:
                task_files = task.get('files', [])
                filtered_files = [file_ref for file_ref in task_files if file_ref.get('file_id') != file_id]
                if len(filtered_files) != len(task_files):
                    task['files'] = filtered_files
                    changed = True

            if changed:
                projects_ref.document(doc.id).update({
                    'project_files': project_files,
                    'tasks': tasks,
                })

        delete_drive_file_record(file_id)
        return {'success': True}
    except Exception as error:
        print(f'Error removing drive file references: {error}')
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