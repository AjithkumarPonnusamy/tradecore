import os
import shutil
import json
from typing import Dict, Optional
from fastapi import UploadFile
from sqlalchemy.orm import Session
from app.models.models import User
from app.core.config import settings

# For fallback/local development storage
LOCAL_UPLOAD_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "local_uploads"
)

# Ensure local upload directory exists
os.makedirs(LOCAL_UPLOAD_DIR, exist_ok=True)

class GoogleDriveService:
    def __init__(self):
        self.creds_configured = False
        self.service = None
        
        # 1. Try Service Account JSON string from environment variable
        if hasattr(settings, "GOOGLE_SERVICE_ACCOUNT_JSON") and settings.GOOGLE_SERVICE_ACCOUNT_JSON:
            try:
                from google.oauth2 import service_account
                from googleapiclient.discovery import build
                
                info = json.loads(settings.GOOGLE_SERVICE_ACCOUNT_JSON)
                credentials = service_account.Credentials.from_service_account_info(
                    info,
                    scopes=['https://www.googleapis.com/auth/drive']
                )
                self.service = build('drive', 'v3', credentials=credentials)
                self.creds_configured = True
                print("Google Drive Service initialized successfully via Service Account JSON string.")
            except Exception as e:
                print(f"Failed to initialize Google Drive service via Service Account JSON string: {e}")
                self.creds_configured = False

        # 2. Try Service Account credentials file
        elif hasattr(settings, "GOOGLE_CREDENTIALS_FILE") and settings.GOOGLE_CREDENTIALS_FILE and os.path.exists(settings.GOOGLE_CREDENTIALS_FILE):
            try:
                from google.oauth2 import service_account
                from googleapiclient.discovery import build
                
                credentials = service_account.Credentials.from_service_account_file(
                    settings.GOOGLE_CREDENTIALS_FILE,
                    scopes=['https://www.googleapis.com/auth/drive']
                )
                self.service = build('drive', 'v3', credentials=credentials)
                self.creds_configured = True
                print(f"Google Drive Service initialized successfully via file: {settings.GOOGLE_CREDENTIALS_FILE}")
            except Exception as e:
                print(f"Failed to initialize Google Drive service via file {settings.GOOGLE_CREDENTIALS_FILE}: {e}")
                self.creds_configured = False

    def _ensure_user_service(self, user_id: str, db: Session) -> bool:
        """Configure self.service for a specific user using stored OAuth tokens.
        Returns True if a service is ready, otherwise False (fallback to local storage)."""
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            print(f"User {user_id} not found for Google Drive service.")
            return False
        
        if user.google_access_token:
            try:
                # Set default expiry if missing
                expiry = user.google_token_expiry
                
                creds = Credentials(
                    token=user.google_access_token,
                    refresh_token=user.google_refresh_token,
                    token_uri='https://oauth2.googleapis.com/token',
                    client_id=user.google_client_id or settings.GOOGLE_CLIENT_ID,
                    client_secret=user.google_client_secret or settings.GOOGLE_CLIENT_SECRET,
                    scopes=['https://www.googleapis.com/auth/drive.file'],
                    expiry=expiry
                )
                if creds.expired and creds.refresh_token:
                    print(f"Refreshing Google access token for user {user_id}...")
                    creds.refresh(Request())
                    # Save refreshed token and expiry time
                    user.google_access_token = creds.token
                    user.google_token_expiry = creds.expiry
                    db.commit()
                self.service = build('drive', 'v3', credentials=creds)
                self.creds_configured = True
                return True
            except Exception as e:
                print(f"Failed to build Google Drive service for user {user_id}: {e}")
                return False
        else:
            print(f"No OAuth access token stored for user {user_id}; using local fallback.")
            return False

    def get_or_create_folder(self, service) -> Optional[str]:
        """Finds or creates a folder in Google Drive. Returns its folder ID."""
        folder_name = getattr(settings, "GOOGLE_DRIVE_FOLDER_NAME", "Trade Journal")
        try:
            # 1. Search for existing folder named folder_name
            query = f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}' and trashed=false"
            response = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
            files = response.get('files', [])
            if files:
                return files[0].get('id')

            # 2. Create folder if not found
            folder_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            folder = service.files().create(body=folder_metadata, fields='id').execute()
            return folder.get('id')
        except Exception as e:
            print(f"Error getting/creating folder '{folder_name}': {e}")
            return None

    def upload_image(self, file: UploadFile, category: str, user_id: Optional[str] = None, db: Optional[Session] = None) -> Dict[str, str]:
        """
        Uploads image file. If user-specific service available, uses it; otherwise falls back to system service or local.
        """
        # Validate file size (limit: 10MB)
        MAX_SIZE = 10 * 1024 * 1024
        file.file.seek(0, os.SEEK_END)
        file_size = file.file.tell()
        file.file.seek(0)
        
        if file_size > MAX_SIZE:
            raise ValueError("Maximum file size allowed is 10MB.")
            
        # Validate mimetype (must be an image)
        if not file.content_type or not file.content_type.startswith("image/"):
            raise ValueError("Only image files are allowed.")
            
        filename = f"{category}_{os.urandom(4).hex()}_{file.filename}"
        
        service = None
        user = None
        if user_id and db:
            self._ensure_user_service(user_id, db)
            service = self.service
            user = db.query(User).filter(User.id == user_id).first()
        
        if not service and self.creds_configured:
            service = self.service

        if service:
            try:
                # Find/Create user's Google Drive folder if not already saved
                folder_id = None
                if user:
                    if not user.google_drive_folder_id:
                        folder_id = self.get_or_create_folder(service)
                        if folder_id:
                            user.google_drive_folder_id = folder_id
                            db.commit()
                    else:
                        folder_id = user.google_drive_folder_id

                from googleapiclient.http import MediaIoBaseUpload
                
                file_metadata = {'name': filename}
                if folder_id:
                    file_metadata['parents'] = [folder_id]
                elif settings.GOOGLE_DRIVE_FOLDER_ID:
                    file_metadata['parents'] = [settings.GOOGLE_DRIVE_FOLDER_ID]
                
                file.file.seek(0)
                media = MediaIoBaseUpload(file.file, mimetype=file.content_type, resumable=True)
                
                drive_file = service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id, webViewLink'
                ).execute()
                
                file_id = drive_file.get("id")
                
                try:
                    service.permissions().create(
                        fileId=file_id,
                        body={'type': 'anyone', 'role': 'reader'}
                    ).execute()
                except Exception as perm_err:
                    print(f"Failed to set Google Drive file permissions to public: {perm_err}")
                
                return {
                    "file_id": file_id,
                    "file_url": f"https://docs.google.com/uc?export=view&id={file_id}"
                }
            except Exception as e:
                print(f"Error uploading to Google Drive: {e}")
        
        file_path = os.path.join(LOCAL_UPLOAD_DIR, filename)
        file.file.seek(0)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        return {
            "file_id": f"local_{os.urandom(8).hex()}",
            "file_url": f"/static/uploads/{filename}"
        }

    def delete_image(self, file_id: str, user_id: Optional[str] = None, db: Optional[Session] = None) -> bool:
        """Delete image either from Google Drive (per‑user) or local fallback."""
        if not file_id:
            return True
        if file_id.startswith("local_"):
            return True
        
        service = None
        if user_id and db:
            self._ensure_user_service(user_id, db)
            service = self.service
        if not service and self.creds_configured:
            service = self.service
        
        if service:
            try:
                service.files().delete(fileId=file_id).execute()
                return True
            except Exception as e:
                print(f"Error deleting file {file_id} from Google Drive: {e}")
                return False
        return True

drive_service = GoogleDriveService()
