from .google_services import (create_project_firestore, create_project_gcalendar, create_task_gcalendar, 
    get_project_by_uid, get_tasks_for_project_user, get_users, get_projects_for_user, update_task_status, 
    add_task_to_project, update_project_status, TASK_STATUSES, PROJECT_STATUSES, 
    VALID_TASK_TRANSITIONS, VALID_PROJECT_TRANSITIONS, sync_task_to_google_calendar)
from flask import Blueprint, render_template, redirect, session, url_for, request, jsonify
from datetime import datetime

from app import inject_session_data
from .decorators import auth_required

# Create a blueprint named 'projects'
projects_bp = Blueprint('projects', __name__, url_prefix='/')

@projects_bp.route('/', methods=['GET'])
@auth_required
def projects():
    user = {
        "uid": session["uid"],
        "email": session["email"],
        "name": session["name"],
        "picture": session["picture"],
        "current_session_id": session["current_session_id"]
    }
    members = get_users()
    projects = get_projects_for_user(user['uid'])
    for project in projects:
        project['tasks'] = get_tasks_for_project_user(project['project_uid'], user['uid'])
    current_year = datetime.now().year
    return render_template("projects.html", user=user, members=members, projects=projects, current_year=current_year)
@projects_bp.route('/create_project', methods=['GET', 'POST'])
@auth_required  
def create_project():
    if request.method == 'POST':
        user = {
            "uid": session["uid"],
            "email": session["email"],
            "name": session["name"],
            "picture": session["picture"],
            "current_session_id": session["current_session_id"]
        }
        project_name = request.form['project-name']
        project_description = request.form['project-description']
        assign_members = request.form.getlist('members')
        project_status = request.form['project-status']
        project_priority = request.form['project-priority']
        project_category = request.form['project-category']
        deadline = request.form['deadline']
        deadline_obj = datetime.strptime(deadline, '%Y-%m-%d')

        start_date = datetime.now().strftime('%Y-%m-%d')
        end_date = deadline_obj.strftime('%Y-%m-%d')
        tasks = []
        i = 1
        while f"tasks[{i}][name]" in request.form:
            tasks.append({
                "name": request.form[f"tasks[{i}][name]"],
                "priority": request.form[f"tasks[{i}][priority]"],
                "status": request.form[f"tasks[{i}][status]"],
                "members": request.form.getlist(f"tasks[{i}][members]"),
                "files": [],
            })
            i += 1

        calendar_link = create_project_gcalendar(project_name, project_description, start_date, end_date)
        if calendar_link is None:
            print("Warning: Failed to create Google Calendar event, proceeding without calendar link")
            calendar_link = ""

        print("DATA:", project_name, assign_members, deadline)
        try:
            result = create_project_firestore(
                user, project_name, project_description, assign_members,
                tasks, project_status, project_priority, project_category,
                calendar_link, start_date, end_date
            )
            print("Project created successfully:", result)
        except Exception as e:
            print(f"Error creating project: {e}")
            # Must pass projects so the template doesn't crash on tojson
            projects = get_projects_for_user(user['uid'])
            for project in projects:
                project['tasks'] = get_tasks_for_project_user(project['project_uid'], user['uid'])
            return render_template("projects.html", 
                user=user, 
                members=get_users(), 
                projects=projects, 
                error="Failed to create project. Please try again."
            )

    return redirect(url_for('projects.projects'))

@projects_bp.route('/update_task_status', methods=['POST'])
@auth_required
def update_task_status_route():
    """Update the status of a specific task"""
    data = request.json
    project_uid = data.get('project_uid')
    task_name = data.get('task_name')
    new_status = data.get('status')
    user_uid = session['uid']

    if not all([project_uid, task_name, new_status]):
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400

    result = update_task_status(project_uid, task_name, new_status, user_uid)
    
    # Sync task status change to Google Calendar
    if result.get('success'):
        _, project_data = get_project_by_uid(project_uid)
        if project_data:
            project_name = project_data.get('project_name', 'Project')
            # Construct task event ID (typically project_uid_taskname)
            task_event_id = f"{project_uid}_{task_name}".replace(' ', '_')
            sync_task_to_google_calendar(task_event_id, task_name, project_name, new_status)
    
    return jsonify(result)

@projects_bp.route('/add_task', methods=['POST'])
@auth_required
def add_task_route():
    """Add a new task to an existing project"""
    data = request.json
    project_uid = data.get('project_uid')
    task_name = data.get('name')
    task_priority = data.get('priority', 'medium')
    task_status = data.get('status', 'todo')
    task_due_date = data.get('due_date')
    task_members = data.get('members', [])
    user_uid = session['uid']

    if not all([project_uid, task_name]):
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400

    if user_uid not in task_members:
        task_members.append(user_uid)

    project_id, project_data = get_project_by_uid(project_uid)
    if not project_data:
        return jsonify({'success': False, 'message': 'Project not found'}), 404

    if not task_due_date:
        task_due_date = project_data.get('end_date')

    task_data = {
        'name': task_name,
        'priority': task_priority,
        'status': task_status,
        'due_date': task_due_date,
        'members': task_members,
        'files': [],
        'event_link': '',
        'event_id': ''
    }

    if task_due_date:
        event_data = create_task_gcalendar(task_name, project_data.get('project_name', ''), task_due_date, project_data.get('project_description', ''))
        if event_data:
            task_data['event_link'] = event_data.get('htmlLink', '')
            task_data['event_id'] = event_data.get('id', '')

    result = add_task_to_project(project_uid, task_data, user_uid)
    return jsonify(result)

@projects_bp.route('/update_project_status', methods=['POST'])
@auth_required
def update_project_status_route():
    """Update the status of a project"""
    data = request.json
    project_uid = data.get('project_uid')
    new_status = data.get('status')
    user_uid = session['uid']

    if not all([project_uid, new_status]):
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400

    result = update_project_status(project_uid, new_status, user_uid)
    return jsonify(result)

@projects_bp.route('/get_project_tasks/<project_uid>', methods=['GET'])
@auth_required
def get_project_tasks(project_uid):
    """Get all tasks for a specific project"""
    user_uid = session['uid']
    tasks = get_tasks_for_project_user(project_uid, user_uid)
    return jsonify({'success': True, 'tasks': tasks})

@projects_bp.route('/api/status_info', methods=['GET'])
@auth_required
def get_status_info():
    """Get available statuses and valid transitions"""
    return jsonify({
        'success': True,
        'project_statuses': PROJECT_STATUSES,
        'task_statuses': TASK_STATUSES,
        'valid_project_transitions': VALID_PROJECT_TRANSITIONS,
        'valid_task_transitions': VALID_TASK_TRANSITIONS
    })

@projects_bp.route('/api/project_status_transitions/<project_uid>', methods=['GET'])
@auth_required
def get_project_status_transitions(project_uid):
    """Get valid status transitions for a specific project"""
    user_uid = session['uid']
    doc_id, project_data = get_project_by_uid(project_uid)
    
    if not project_data:
        return jsonify({'success': False, 'message': 'Project not found'}), 404
    
    if user_uid not in project_data.get('assigned_members', []):
        return jsonify({'success': False, 'message': 'Not authorized'}), 403
    
    current_status = project_data.get('status', 'planning')
    valid_transitions = VALID_PROJECT_TRANSITIONS.get(current_status, [])
    
    return jsonify({
        'success': True,
        'current_status': current_status,
        'valid_transitions': valid_transitions
    })

@projects_bp.route('/api/task_status_transitions/<project_uid>/<task_name>', methods=['GET'])
@auth_required
def get_task_status_transitions(project_uid, task_name):
    """Get valid status transitions for a specific task"""
    user_uid = session['uid']
    doc_id, project_data = get_project_by_uid(project_uid)
    
    if not project_data:
        return jsonify({'success': False, 'message': 'Project not found'}), 404
    
    if user_uid not in project_data.get('assigned_members', []):
        return jsonify({'success': False, 'message': 'Not authorized'}), 403
    
    # Find the task
    task = None
    for t in project_data.get('tasks', []):
        if t.get('name') == task_name:
            task = t
            break
    
    if not task:
        return jsonify({'success': False, 'message': 'Task not found'}), 404
    
    current_status = task.get('status', 'todo')
    valid_transitions = VALID_TASK_TRANSITIONS.get(current_status, [])
    
    return jsonify({
        'success': True,
        'current_status': current_status,
        'valid_transitions': valid_transitions
    })