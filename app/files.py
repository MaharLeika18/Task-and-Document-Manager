from flask import Blueprint, jsonify, redirect, render_template, request, send_file, session
from datetime import datetime
from .decorators import auth_required
from .google_drive_services import (
    create_drive_folder,
    download_drive_file,
    get_drive_file_metadata,
    list_drive_items,
    upload_file_to_drive,
)
from .google_services import (
    get_project_file_references,
    get_projects_for_user,
    get_tasks_for_project_user,
    link_drive_file_to_project_task,
)

# Create a blueprint named 'files'
files_bp = Blueprint('files', __name__, url_prefix='/')

@files_bp.route('/files', methods=['GET'])
@auth_required
def files():
    user = {
        "uid": session["uid"],
        "email": session["email"],
        "name": session["name"],
        "picture": session["picture"],
        "current_session_id": session["current_session_id"]
    }
    projects = get_projects_for_user(user['uid'])
    for project in projects:
        project['tasks'] = get_tasks_for_project_user(project['project_uid'], user['uid'])

    return render_template("files.html", user=user, projects=projects)


@files_bp.route('/api/list', methods=['GET'])
@auth_required
def list_files_route():
    folder_id = request.args.get('folder_id')
    project_uid = request.args.get('project_uid')
    user_uid = session['uid']

    items = list_drive_items(folder_id)
    references = None
    if project_uid:
        references = get_project_file_references(project_uid, user_uid)

    return jsonify({'success': True, 'items': items, 'references': references})


@files_bp.route('/api/create_folder', methods=['POST'])
@auth_required
def create_folder_route():
    data = request.json or {}
    name = (data.get('name') or '').strip()
    parent_folder_id = data.get('parent_folder_id')

    if not name:
        return jsonify({'success': False, 'message': 'Folder name is required'}), 400

    result = create_drive_folder(name, parent_folder_id)
    return jsonify(result), 200 if result.get('success') else 500


@files_bp.route('/api/upload', methods=['POST'])
@auth_required
def upload_file_route():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file part in request'}), 400

    file_storage = request.files.get('file')
    folder_id = request.form.get('folder_id')
    project_uid = request.form.get('project_uid')
    task_name = request.form.get('task_name') or None
    user_uid = session['uid']

    upload_result = upload_file_to_drive(file_storage, folder_id)
    if not upload_result.get('success'):
        return jsonify(upload_result), 500

    link_result = None
    if project_uid:
        link_result = link_drive_file_to_project_task(
            project_uid,
            upload_result['file'],
            user_uid,
            task_name=task_name
        )

    return jsonify({
        'success': True,
        'file': upload_result['file'],
        'link_result': link_result
    })


@files_bp.route('/api/link', methods=['POST'])
@auth_required
def link_existing_file_route():
    data = request.json or {}
    file_id = data.get('file_id')
    project_uid = data.get('project_uid')
    task_name = data.get('task_name') or None
    user_uid = session['uid']

    if not file_id or not project_uid:
        return jsonify({'success': False, 'message': 'file_id and project_uid are required'}), 400

    metadata_result = get_drive_file_metadata(file_id)
    if not metadata_result.get('success'):
        return jsonify(metadata_result), 500

    result = link_drive_file_to_project_task(
        project_uid,
        metadata_result['file'],
        user_uid,
        task_name=task_name
    )
    return jsonify(result), 200 if result.get('success') else 400


@files_bp.route('/api/project_refs/<project_uid>', methods=['GET'])
@auth_required
def get_project_refs_route(project_uid):
    user_uid = session['uid']
    result = get_project_file_references(project_uid, user_uid)
    return jsonify(result), 200 if result.get('success') else 404


@files_bp.route('/view/<file_id>', methods=['GET'])
@auth_required
def view_file_route(file_id):
    result = get_drive_file_metadata(file_id)
    if not result.get('success'):
        return jsonify(result), 404

    file_data = result['file']
    target = file_data.get('web_view_link') or file_data.get('web_content_link')
    if not target:
        return jsonify({'success': False, 'message': 'No preview link available'}), 404

    return redirect(target)


@files_bp.route('/download/<file_id>', methods=['GET'])
@auth_required
def download_file_route(file_id):
    result = download_drive_file(file_id)
    if not result.get('success'):
        return jsonify(result), 404

    return send_file(
        result['file_obj'],
        as_attachment=True,
        download_name=result['filename'],
        mimetype=result['mime_type']
    )