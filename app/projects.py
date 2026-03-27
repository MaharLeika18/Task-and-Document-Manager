from .google_services import create_project_firestore, create_project_gcalendar, get_tasks_for_project_user, get_users, get_projects_for_user
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
    return render_template("projects.html", user=user, members=members, projects=projects)
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
        print("DATA:", project_name, assign_members, deadline)
        try:
            create_project_firestore(
                user, project_name, project_description, assign_members,
                tasks, project_status, project_priority, project_category,
                calendar_link, start_date, end_date
            )
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