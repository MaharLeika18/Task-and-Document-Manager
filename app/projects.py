from .google_services import create_project_firestore, create_project_gcalendar, get_tasks_for_project_user, get_users, get_projects_for_user, update_task_status, add_task_to_project, update_project_status
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
    task_members = data.get('members', [])
    user_uid = session['uid']

    if not all([project_uid, task_name]):
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400

    # Ensure current user is included in task members if not already
    if user_uid not in task_members:
        task_members.append(user_uid)

    task_data = {
        'name': task_name,
        'priority': task_priority,
        'status': task_status,
        'members': task_members
    }

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