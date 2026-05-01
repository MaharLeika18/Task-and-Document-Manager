import io
import os

import dotenv
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
from .firebase_run import db

dotenv.load_dotenv()

DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive"]


def gdrive_service():
    token_file = os.getenv('COUNCILOG_TOKEN_FILE', 'token.json')
    oauth_file = os.getenv('COUNCILOG_OAUTH_FILE')
    service_account_file = os.getenv('COUNCILOG_SERVICE_ACCOUNT_FILE')
    creds = None

    try:
        if token_file and os.path.exists(token_file):
            creds = Credentials.from_authorized_user_file(token_file, DRIVE_SCOPES)

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(token_file, 'w', encoding='utf-8') as token:
                token.write(creds.to_json())

        if not creds or not creds.valid:
            if oauth_file and os.path.exists(oauth_file):
                flow = InstalledAppFlow.from_client_secrets_file(oauth_file, DRIVE_SCOPES)
                creds = flow.run_local_server(port=0)
                with open(token_file, 'w', encoding='utf-8') as token:
                    token.write(creds.to_json())
            elif service_account_file and os.path.exists(service_account_file):
                creds = service_account.Credentials.from_service_account_file(
                    service_account_file,
                    scopes=DRIVE_SCOPES
                )
            else:
                raise RuntimeError('No valid Google Drive credentials found.')

        return build('drive', 'v3', credentials=creds)
    except Exception as error:
        print(f'Error creating Google Drive service: {error}')
        raise


def _serialize_drive_item(item):
    mime_type = item.get('mimeType', '')
    file_name = item.get('name', '')
    parents = item.get('parents', []) or []
    
    return {
        'file_id': item.get('id', ''),
        'name': file_name,
        'mime_type': mime_type,
        'size': item.get('size', '0'),
        'modified_time': item.get('modifiedTime', ''),
        'web_view_link': item.get('webViewLink', ''),
        'web_content_link': item.get('webContentLink', ''),
        'icon_link': item.get('iconLink', ''),
        'parent_id': parents[0] if parents else '',
        'is_folder': mime_type == 'application/vnd.google-apps.folder',
        'is_exportable': _is_exportable_format(mime_type, file_name)
    }


def _is_exportable_format(mime_type, file_name):
    """Check if a file can be exported/previewed by Google Drive."""
    exportable_mimes = [
        'application/vnd.google-apps.document',
        'application/vnd.google-apps.spreadsheet',
        'application/vnd.google-apps.presentation',
        'application/vnd.google-apps.form',
        'application/vnd.google-apps.drawing',
    ]
    
    exportable_extensions = [
        '.pdf', '.docx', '.doc', '.xlsx', '.xls', '.pptx', '.ppt',
        '.txt', '.csv', '.json', '.xml', '.html',
        '.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg',
        '.zip', '.rar', '.7z'
    ]
    
    if mime_type in exportable_mimes:
        return True
    
    file_name_lower = (file_name or '').lower()
    return any(file_name_lower.endswith(ext) for ext in exportable_extensions)


def list_drive_items(folder_id=None):
    try:
        service = gdrive_service()
        parent_folder = folder_id or os.getenv('COUNCILOG_GDRIVE_FOLDER_ID')

        if not parent_folder:
            return []

        query = f"'{parent_folder}' in parents and trashed = false"
        response = service.files().list(
            q=query,
            fields='files(id,name,mimeType,size,modifiedTime,webViewLink,webContentLink,iconLink,parents)',
            pageSize=200,
            orderBy='folder,name'
        ).execute()

        return [_serialize_drive_item(item) for item in response.get('files', [])]
    except Exception as error:
        print(f'Error listing Google Drive files: {error}')
        return []


def create_project_folder(project_name, project_uid):
    """Create a dedicated Google Drive folder for a project."""
    try:
        service = gdrive_service()
        parent_folder = os.getenv('COUNCILOG_GDRIVE_FOLDER_ID')
        
        if not parent_folder:
            return {
                'success': False,
                'message': 'No root Drive folder configured'
            }
        
        # Create folder with project name and UID for uniqueness
        folder_name = f"{project_name} ({project_uid[:8]})"
        metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_folder]
        }
        
        created = service.files().create(
            body=metadata,
            fields='id,name,webViewLink'
        ).execute()
        
        return {
            'success': True,
            'folder_id': created.get('id'),
            'folder_name': created.get('name'),
            'web_view_link': created.get('webViewLink')
        }
    except Exception as error:
        print(f'Error creating project folder: {error}')
        return {
            'success': False,
            'message': str(error)
        }
def create_drive_folder(name, parent_folder_id=None):
    try:
        service = gdrive_service()
        parent = parent_folder_id or os.getenv('COUNCILOG_GDRIVE_FOLDER_ID')
        metadata = {
            'name': name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        if parent:
            metadata['parents'] = [parent]

        created = service.files().create(
            body=metadata,
            fields='id,name,mimeType,modifiedTime,webViewLink'
        ).execute()

        return {
            'success': True,
            'folder': _serialize_drive_item(created)
        }
    except Exception as error:
        print(f'Error creating Google Drive folder: {error}')
        return {
            'success': False,
            'message': str(error)
        }


def upload_file_to_drive(file_storage, folder_id=None):
    try:
        if not file_storage or not file_storage.filename:
            return {
                'success': False,
                'message': 'No file selected'
            }

        service = gdrive_service()
        parent = folder_id or os.getenv('COUNCILOG_GDRIVE_FOLDER_ID')

        file_storage.stream.seek(0)
        media = MediaIoBaseUpload(
            file_storage.stream,
            mimetype=file_storage.mimetype or 'application/octet-stream',
            resumable=False
        )
        metadata = {'name': file_storage.filename}
        if parent:
            metadata['parents'] = [parent]

        created = service.files().create(
            body=metadata,
            media_body=media,
            fields='id,name,mimeType,size,modifiedTime,webViewLink,webContentLink,iconLink'
        ).execute()

        return {
            'success': True,
            'file': _serialize_drive_item(created)
        }
    except Exception as error:
        print(f'Error uploading file to Google Drive: {error}')
        return {
            'success': False,
            'message': str(error)
        }


def get_drive_file_metadata(file_id):
    try:
        service = gdrive_service()
        data = service.files().get(
            fileId=file_id,
            fields='id,name,mimeType,size,modifiedTime,webViewLink,webContentLink,iconLink,parents'
        ).execute()
        return {
            'success': True,
            'file': _serialize_drive_item(data)
        }
    except Exception as error:
        print(f'Error fetching Google Drive file metadata: {error}')
        return {
            'success': False,
            'message': str(error)
        }

def get_drive_folder_metadata(folder_id):
    try:
        service = gdrive_service()
        data = service.files().get(
            fileId=folder_id,
            fields='id,name,mimeType,parents'
        ).execute()
        return {
            'success': True,
            'folder': _serialize_drive_item(data)
        }
    except Exception as error:
        print(f'Error fetching Google Drive folder metadata: {error}')
        return {
            'success': False,
            'message': str(error)
        }


def delete_drive_item(file_id):
    try:
        service = gdrive_service()
        service.files().update(
            fileId=file_id,
            body={'trashed': True}
        ).execute()
        return {
            'success': True,
            'message': 'Item moved to trash successfully'
        }
    except Exception as error:
        print(f'Error deleting Google Drive item: {error}')
        return {
            'success': False,
            'message': str(error)
        }


def stream_drive_file(file_id, export_mime=None):
    try:
        service = gdrive_service()
        metadata = service.files().get(fileId=file_id, fields='id,name,mimeType').execute()
        mime_type = metadata.get('mimeType', 'application/octet-stream')

        if export_mime and mime_type.startswith('application/vnd.google-apps'):
            request = service.files().export_media(fileId=file_id, mimeType=export_mime)
            mime_type = export_mime
        else:
            request = service.files().get_media(fileId=file_id)

        output = io.BytesIO()
        downloader = MediaIoBaseDownload(output, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()

        output.seek(0)
        return {
            'success': True,
            'file_obj': output,
            'filename': metadata.get('name', 'downloaded-file'),
            'mime_type': mime_type
        }
    except Exception as error:
        print(f'Error streaming Google Drive file: {error}')
        return {
            'success': False,
            'message': str(error)
        }


def download_drive_file(file_id):
    try:
        service = gdrive_service()
        metadata = service.files().get(fileId=file_id, fields='id,name,mimeType').execute()
        request = service.files().get_media(fileId=file_id)

        output = io.BytesIO()
        downloader = MediaIoBaseDownload(output, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()

        output.seek(0)
        return {
            'success': True,
            'file_obj': output,
            'filename': metadata.get('name', 'downloaded-file'),
            'mime_type': metadata.get('mimeType', 'application/octet-stream')
        }
    except Exception as error:
        print(f'Error downloading Google Drive file: {error}')
        return {
            'success': False,
            'message': str(error)
        }


def upload_profile_photo_to_drive(file_storage, user_uid):
    """Upload a profile photo to Google Drive and return the file ID."""
    try:
        if not file_storage or not file_storage.filename:
            return {
                'success': False,
                'message': 'No file selected'
            }

        # Validate that it's an image file
        if file_storage.mimetype and not file_storage.mimetype.startswith('image/'):
            return {
                'success': False,
                'message': 'Only image files are allowed'
            }

        service = gdrive_service()

        # Get folder ID from Firestore
        config_ref = db.collection("app_config").document("drive")
        config_doc = config_ref.get()

        profile_photos_folder_id = None
        if config_doc.exists:
            profile_photos_folder_id = config_doc.to_dict().get("profile_photos_folder_id")        

        if not profile_photos_folder_id:
            # Create profile photos folder if it doesn't exist
            parent_folder = os.getenv('COUNCILOG_GDRIVE_FOLDER_ID')
            folder_result = create_drive_folder('Profile Photos', parent_folder)
            
            folder = folder_result.get('folder', {})

            profile_photos_folder_id = (
                folder.get('file_id') or 
                folder.get('id')
            )

            # Save folder ID to Firestore
            db.collection("app_config").document("drive").set({
                "profile_photos_folder_id": profile_photos_folder_id
            }, merge=True)

            if not profile_photos_folder_id:
                return {
                    'success': False,
                    'message': 'Folder ID missing'
            }

        # Create user-specific folder or use user_uid as part of filename
        filename = f"{user_uid}_{file_storage.filename}"
        
        file_storage.stream.seek(0)
        media = MediaIoBaseUpload(
            file_storage.stream,
            mimetype=file_storage.mimetype or 'application/octet-stream',
            resumable=False
        )
        metadata = {
            'name': filename,
            'parents': [profile_photos_folder_id]
        }

        created = service.files().create(
            body=metadata,
            media_body=media,
            fields='id,name,webViewLink,webContentLink'
        ).execute()

        file_id = created.get('id')
        drive_url = f"https://lh3.googleusercontent.com/d/{file_id}"

        # Make file public
        service.permissions().create(
            fileId=created.get('id'),
            body={
                'type': 'anyone',
                'role': 'reader'
            }
        ).execute()

        # Update user profile
        db.collection("users").document(user_uid).update({
            "picture": drive_url
        })

        return {
            'success': True,
            'file_id': file_id,
            'picture_url': drive_url,
            'file': _serialize_drive_item(created)
        }    
        
    except Exception as error:
        print(f'Error uploading profile photo to Google Drive: {error}')
        return {
            'success': False,
            'message': str(error)
        }