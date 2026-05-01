from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from datetime import datetime
from .decorators import auth_required
from .google_drive_services import upload_profile_photo_to_drive
from .google_services import (
    delete_user_account,
    get_member_summaries,
    get_projects_for_user,
    get_user_profile,
    get_users,
    update_user_profile,
)
from .firebase_run import db

# Create a blueprint named 'members'
members_bp = Blueprint('members', __name__, url_prefix='/')

@members_bp.route('/members', methods=['GET'])
@auth_required
def members():
    user = {
        "uid": session["uid"],
        "email": session["email"],
        "name": session["name"],
        "picture": session["picture"],
        "current_session_id": session["current_session_id"]
    }
    members = get_users()
    member_summaries = get_member_summaries()

    for member in members:
        if member.get('uid') == user['uid'] and not member.get('picture'):
            member['picture'] = user.get('picture', '')
        summary = member_summaries.get(member['uid'], {
            'projects_count': 0,
            'tasks_count': 0,
            'open_tasks_count': 0,
            'completed_tasks_count': 0
        })
        member.update(summary)

    return render_template("members.html", user=user, members=members)


@members_bp.route('/profile', methods=['GET', 'POST'])
@auth_required
def profile():
    user = {
        "uid": session["uid"],
        "email": session["email"],
        "name": session["name"],
        "picture": session["picture"],
        "current_session_id": session["current_session_id"]
    }

    profile_result = get_user_profile(user['uid'])
    if not profile_result.get('success'):
        flash(profile_result.get('message', 'Unable to load your profile.'), 'error')
        profile_data = {
            'uid': user['uid'],
            'name': user['name'],
            'display_name': user['name'],
            'username': user['name'],
            'email': user['email'],
            'picture': user['picture'],
            'photo_source': 'google',
            'date_created': '',
            'role': 'Member',
        }
    else:
        profile_data = profile_result['user']

    project_count = 0
    task_count = 0
    projects = get_projects_for_user(user['uid'])
    project_count = len(projects)
    for project in projects:
        for task in project.get('tasks', []):
            if user['uid'] in task.get('members', []):
                task_count += 1

    if request.method == 'POST':
        display_name = request.form.get('display_name', '').strip()
        picture_url = request.form.get('picture_url', '').strip()
        photo_action = request.form.get('photo_action', 'save')
        photo_source = 'custom'
 
        # Handle file upload
        if 'profile_photo' in request.files and request.files['profile_photo'].filename:
            file_storage = request.files.get('profile_photo')
            upload_result = upload_profile_photo_to_drive(file_storage, user['uid'])
            if upload_result.get('success'):
                session["picture"] = upload_result["picture_url"] 
                picture_url = upload_result["picture_url"]  
                db.collection("users").document(user['uid']).update({
                    "picture": picture_url,
                    "photo_source": "custom"
                })
                photo_source = 'custom'
                flash('Profile photo uploaded successfully.', 'success')
            else:
                flash(upload_result.get('message', 'Failed to upload profile photo.'), 'error')
        elif photo_action == 'google':
            # Get google photo 
            user_doc = db.collection("users").document(user['uid']).get()

            google_picture = ""
            if user_doc.exists:
                google_picture = user_doc.to_dict().get("google_picture", "")

            if not google_picture:
                flash("No Google profile picture found.", "error")
            else:
                picture_url = google_picture
                photo_source = 'google'

                # Update session
                session["picture"] = picture_url

                # Update active picture
                db.collection("users").document(user['uid']).update({
                    "picture": picture_url,
                    "photo_source": "google"
                })

                flash("Switched to Google profile picture.", "success")
        else:
            photo_source = 'google' if picture_url and picture_url == session.get('picture', '') else 'custom'

        result = update_user_profile(
            user['uid'],
            display_name=display_name or profile_data.get('display_name') or profile_data.get('name') or user['name'],
            picture=picture_url,
            photo_source=photo_source,
        )

        if result.get('success'):
            updated_user = result.get('user', {})
            session['name'] = updated_user.get('name', session['name'])
            session['picture'] = updated_user.get('picture', session['picture'])
            flash('Profile updated successfully.', 'success')
            return redirect(url_for('members.profile'))

        flash(result.get('message', 'Could not update profile.'), 'error')

    return render_template(
        'profile.html',
        user=user,
        profile=profile_data,
        projects=projects,
        project_count=project_count,
        task_count=task_count,
    )


@members_bp.route('/profile/delete', methods=['POST'])
@auth_required
def profile_delete():
    uid = session['uid']
    result = delete_user_account(uid)
    session.clear()

    return redirect(url_for('login.index'))
