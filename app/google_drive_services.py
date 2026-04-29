import io
import os

import dotenv
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload

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
    
    return {
        'file_id': item.get('id', ''),
        'name': file_name,
        'mime_type': mime_type,
        'size': item.get('size', '0'),
        'modified_time': item.get('modifiedTime', ''),
        'web_view_link': item.get('webViewLink', ''),
        'web_content_link': item.get('webContentLink', ''),
        'icon_link': item.get('iconLink', ''),
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
            fields='files(id,name,mimeType,size,modifiedTime,webViewLink,webContentLink,iconLink)',
            pageSize=200,
            orderBy='folder,name'
        ).execute()

        return [_serialize_drive_item(item) for item in response.get('files', [])]
    except Exception as error:
        print(f'Error listing Google Drive files: {error}')
        return []


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
            fields='id,name,mimeType,size,modifiedTime,webViewLink,webContentLink,iconLink'
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