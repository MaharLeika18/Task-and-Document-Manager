from flask import Blueprint, jsonify, redirect, render_template, request, send_file, session, url_for
from urllib.parse import urlencode
from datetime import datetime
import io
from googleapiclient.http import MediaIoBaseDownload
from .decorators import auth_required
from .google_drive_services import (
    create_drive_folder,
    delete_drive_item,
    download_drive_file,
    get_drive_folder_metadata,
    get_drive_file_metadata,
    list_drive_items,
    stream_drive_file,
    upload_file_to_drive,
    gdrive_service,
)
from .google_services import (
    get_project_by_uid,
    get_project_file_references,
    get_projects_for_user,
    get_tasks_for_project_user,
    link_drive_file_to_project_task,
    remove_drive_file_references,
    upsert_drive_file_record,
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
    current_folder = None

    # If project_uid provided and no explicit folder_id, use project's dedicated folder
    if project_uid and not folder_id:
        doc_id, project_data = get_project_by_uid(project_uid)
        if project_data and project_data.get('drive_folder_id'):
            folder_id = project_data.get('drive_folder_id')

    items = list_drive_items(folder_id)
    if folder_id:
        folder_result = get_drive_folder_metadata(folder_id)
        if folder_result.get('success'):
            current_folder = folder_result.get('folder')

    references = None
    if project_uid:
        references_result = get_project_file_references(project_uid, user_uid)
        references = references_result if references_result.get('success') else None

    return jsonify({'success': True, 'items': items, 'references': references, 'current_folder': current_folder})


@files_bp.route('/api/create_folder', methods=['POST'])
@auth_required
def create_folder_route():
    data = request.json or {}
    name = (data.get('name') or '').strip()
    parent_folder_id = data.get('parent_folder_id')
    project_uid = data.get('project_uid')

    if not name:
        return jsonify({'success': False, 'message': 'Folder name is required'}), 400

    # If project_uid provided and no explicit parent, use project's folder
    if project_uid and not parent_folder_id:
        from .google_services import get_project_by_uid
        doc_id, project_data = get_project_by_uid(project_uid)
        if project_data and project_data.get('drive_folder_id'):
            parent_folder_id = project_data.get('drive_folder_id')

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

    # If project_uid provided and no explicit folder_id, get the project's dedicated folder
    if project_uid and not folder_id:
        from .google_services import get_project_by_uid
        doc_id, project_data = get_project_by_uid(project_uid)
        if project_data and project_data.get('drive_folder_id'):
            folder_id = project_data.get('drive_folder_id')

    upload_result = upload_file_to_drive(file_storage, folder_id)
    if not upload_result.get('success'):
        return jsonify(upload_result), 500

    upsert_drive_file_record(
        upload_result['file'],
        project_uid=project_uid,
        task_name=task_name,
        linked_by=user_uid,
    )

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


@files_bp.route('/api/delete/<file_id>', methods=['POST'])
@auth_required
def delete_file_route(file_id):
    remove_drive_file_references(file_id)
    result = delete_drive_item(file_id)
    return jsonify(result), 200 if result.get('success') else 500


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
    mime_type = file_data.get('mime_type', '')
    return_project_uid = request.args.get('project_uid') or request.args.get('return_project_uid')
    return_folder_id = request.args.get('folder_id') or request.args.get('return_folder_id')

    return_params = {}
    if return_project_uid:
        return_params['project_uid'] = return_project_uid
    if return_folder_id:
        return_params['folder_id'] = return_folder_id

    return_url = url_for('files.files')
    if return_params:
        return_url = f"{return_url}?{urlencode(return_params)}"
    
    # For images, show in lightbox viewer
    if mime_type.startswith('image/'):
        return render_template('image_viewer.html', 
                             file_id=file_id, 
                             file_name=file_data.get('name', 'Image'),
                             image_src=url_for('files.inline_file_route', file_id=file_id),
                             file_data=file_data,
                             return_url=return_url)
    # For Google Docs/Sheets/Slides, use webViewLink
    elif 'google-apps' in mime_type:
        return render_template(
            'preview.html',
            preview_url=url_for('files.inline_file_route', file_id=file_id, export='pdf'),
            file_name=file_data.get('name', 'Document'),
            file_id=file_id,
            return_url=return_url,
        )
    # For PDF, try webContentLink first, then webViewLink
    elif mime_type in ['application/pdf']:
        return render_template(
            'preview.html',
            preview_url=url_for('files.inline_file_route', file_id=file_id),
            file_name=file_data.get('name', 'Document'),
            file_id=file_id,
            return_url=return_url,
        )
    # For Office documents, embed them in an iframe via Google Viewer
    elif any(fmt in mime_type for fmt in ['word', 'spreadsheet', 'presentation']) or \
         any(ext in mime_type for ext in ['.docx', '.xlsx', '.pptx', '.doc', '.xls', '.ppt']):
        return render_template(
            'preview.html',
            preview_url=url_for('files.inline_file_route', file_id=file_id),
            file_name=file_data.get('name', 'Document'),
            file_id=file_id,
            return_url=return_url,
        )
    # For other file types, try webViewLink (Google Drive preview)
    else:
        return render_template(
            'preview.html',
            preview_url=url_for('files.inline_file_route', file_id=file_id),
            file_name=file_data.get('name', 'Document'),
            file_id=file_id,
            return_url=return_url,
        )


@files_bp.route('/inline/<file_id>', methods=['GET'])
@auth_required
def inline_file_route(file_id):
    export = (request.args.get('export') or '').lower()
    result = get_drive_file_metadata(file_id)
    if not result.get('success'):
        return jsonify(result), 404

    file_data = result['file']
    mime_type = file_data.get('mime_type', 'application/octet-stream')

    if export == 'pdf' and mime_type.startswith('application/vnd.google-apps'):
        stream_result = stream_drive_file(file_id, export_mime='application/pdf')
    else:
        stream_result = stream_drive_file(file_id)

    if not stream_result.get('success'):
        return jsonify(stream_result), 404

    return send_file(
        stream_result['file_obj'],
        as_attachment=False,
        download_name=stream_result.get('filename', file_data.get('name', 'file')),
        mimetype=stream_result.get('mime_type', mime_type)
    )


@files_bp.route('/api/export/<file_id>', methods=['GET'])
@auth_required
def export_file_route(file_id):
    """Get export link for Google Docs/Sheets/Slides."""
    result = get_drive_file_metadata(file_id)
    if not result.get('success'):
        return jsonify(result), 404
    
    file_data = result['file']
    mime_type = file_data.get('mime_type', '')
    
    # Map Google Docs types to export MIME types
    export_formats = {
        'application/vnd.google-apps.document': 'application/pdf',  # or 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        'application/vnd.google-apps.spreadsheet': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/vnd.google-apps.presentation': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    }
    
    export_mime = export_formats.get(mime_type)
    if not export_mime:
        return jsonify({'success': False, 'message': 'File type does not support export'}), 400
    
    try:
        service = gdrive_service()
        export_url = service.files().get_media(fileId=file_id).getbytes
        # Construct the Google Drive export URL
        export_link = f"https://www.googleapis.com/drive/v3/files/{file_id}/export?mimeType={export_mime}"
        return jsonify({
            'success': True,
            'export_url': export_link,
            'export_mime': export_mime,
            'file_name': file_data.get('name', 'document')
        })
    except Exception as error:
        print(f'Error generating export link: {error}')
        return jsonify({'success': False, 'message': str(error)}), 500


@files_bp.route('/download/export/<file_id>', methods=['GET'])
@auth_required
def download_export_route(file_id):
    """Download an exported copy of a Google Doc/Sheet/Slide."""
    export_format = request.args.get('format', 'pdf').lower()
    
    # Map format strings to MIME types
    format_map = {
        'pdf': 'application/pdf',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    }
    
    export_mime = format_map.get(export_format, 'application/pdf')
    
    try:
        service = gdrive_service()
        metadata = service.files().get(fileId=file_id, fields='name,mimeType').execute()
        
        request_obj = service.files().export_media(fileId=file_id, mimeType=export_mime)
        output = io.BytesIO()
        downloader = MediaIoBaseDownload(output, request_obj)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        
        output.seek(0)
        filename = metadata.get('name', 'exported-file')
        ext_map = {
            'application/pdf': '.pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation': '.pptx',
        }
        
        if not any(filename.endswith(ext) for ext in ext_map.values()):
            filename += ext_map.get(export_mime, '')
        
        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype=export_mime
        )
    except Exception as error:
        print(f'Error downloading exported file: {error}')
        return jsonify({'success': False, 'message': str(error)}), 500


@files_bp.route('/download/<file_id>', methods=['GET'])
@auth_required
def download_file_route(file_id):
    result = download_drive_file(file_id)
    if not result.get('success'):
        return jsonify(result), 404

    mime_type = result['mime_type']
    filename = result['filename']
    
    # Ensure proper MIME types for common document formats
    mime_type_map = {
        '.pdf': 'application/pdf',
        '.doc': 'application/msword',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.xls': 'application/vnd.ms-excel',
        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        '.ppt': 'application/vnd.ms-powerpoint',
        '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        '.txt': 'text/plain',
        '.csv': 'text/csv',
        '.json': 'application/json',
        '.xml': 'application/xml',
        '.html': 'text/html',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.webp': 'image/webp',
        '.svg': 'image/svg+xml',
        '.zip': 'application/zip',
        '.rar': 'application/x-rar-compressed',
        '.7z': 'application/x-7z-compressed',
    }
    
    # Check for extension-based MIME type override
    for ext, mime in mime_type_map.items():
        if filename.lower().endswith(ext):
            mime_type = mime
            break
    
    # If still no MIME type, default to octet-stream
    if not mime_type:
        mime_type = 'application/octet-stream'

    return send_file(
        result['file_obj'],
        as_attachment=True,
        download_name=filename,
        mimetype=mime_type
    )