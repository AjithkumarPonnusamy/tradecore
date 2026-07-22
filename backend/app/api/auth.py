import os
from datetime import timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.core.security import verify_password, get_password_hash, create_access_token
from app.models.models import User
from app.schemas.schemas import UserCreate, UserLogin, UserResponse, Token, TokenData, UserUpdate

os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"

GOOGLE_SCOPES = [
    "openid",
    "email",
    "profile",
    "https://www.googleapis.com/auth/drive.file"
]

router = APIRouter(prefix="/auth", tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login-form"
)

def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    

    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(user_id=user_id)
    except JWTError:
        raise credentials_exception
        
    user = db.query(User).filter(User.id == token_data.user_id).first()
    if user is None:
        raise credentials_exception
    return user

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists."
        )
    
    # Create new user
    db_user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        auth_provider="EMAIL",
        is_active=True
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.post("/login", response_model=Token)
def login(login_in: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login_in.email).first()
    if not user or not user.hashed_password or not verify_password(login_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(subject=user.id)
    return {"access_token": access_token, "token_type": "bearer"}

# OAuth2PasswordRequestForm endpoint for FastAPI OpenAPI auto-generated interactive documentation
from fastapi.security import OAuth2PasswordRequestForm
@router.post("/login-form", response_model=Token, include_in_schema=False)
def login_form(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not user.hashed_password or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    access_token = create_access_token(subject=user.id)
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/config")
def get_auth_config():
    """
    Get public auth configuration settings.
    """
    return {
        "google_client_id": settings.GOOGLE_CLIENT_ID,
        "google_drive_folder_name": settings.GOOGLE_DRIVE_FOLDER_NAME,
        "google_scopes": " ".join(GOOGLE_SCOPES)
    }

@router.post("/google", response_model=Token)
def google_auth(payload: dict, db: Session = Depends(get_db)):
    """
    Callback endpoint for Google OAuth login.
    If 'code' is provided, performs the secure exchange to get tokens and user info automatically.
    Otherwise, verifies credential ID token or falls back to direct payload parameters.
    """
    code = payload.get("code")
    google_id = None
    email = None
    name = None
    avatar = None
    access_token = None
    refresh_token = None
    expiry = None

    if code:
        if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Google OAuth is not configured on the server."
            )
        try:
            from google_auth_oauthlib.flow import Flow
            import requests as http_requests
            from google.oauth2 import id_token
            from google.auth.transport import requests as google_requests

            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": settings.GOOGLE_CLIENT_ID,
                        "client_secret": settings.GOOGLE_CLIENT_SECRET,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                    }
                },
                scopes=GOOGLE_SCOPES,
                redirect_uri="postmessage"
            )
            flow.fetch_token(code=code)
            credentials = flow.credentials
            
            access_token = credentials.token
            refresh_token = credentials.refresh_token
            expiry = credentials.expiry
            
            id_token_jwt = credentials.id_token
            if id_token_jwt:
                idinfo = id_token.verify_oauth2_token(
                    id_token_jwt,
                    google_requests.Request(),
                    settings.GOOGLE_CLIENT_ID
                )
                google_id = idinfo.get("sub")
                email = idinfo.get("email")
                name = idinfo.get("name", email.split("@")[0] if email else "Google User")
                avatar = idinfo.get("picture")
            else:
                userinfo_url = "https://www.googleapis.com/oauth2/v3/userinfo"
                headers = {"Authorization": f"Bearer {access_token}"}
                userinfo_resp = http_requests.get(userinfo_url, headers=headers)
                if userinfo_resp.status_code == 200:
                    userinfo = userinfo_resp.json()
                    google_id = userinfo.get("sub")
                    email = userinfo.get("email")
                    name = userinfo.get("name", email.split("@")[0] if email else "Google User")
                    avatar = userinfo.get("picture")
                else:
                    raise Exception("Failed to retrieve Google userinfo")
        except Exception as e:
            print(f"Google authorization code exchange failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Google code exchange failed: {str(e)}"
            )
    else:
        credential = payload.get("credential")
        if credential and settings.GOOGLE_CLIENT_ID:
            try:
                from google.oauth2 import id_token
                from google.auth.transport import requests as google_requests
                
                idinfo = id_token.verify_oauth2_token(
                    credential,
                    google_requests.Request(),
                    settings.GOOGLE_CLIENT_ID
                )
                google_id = idinfo.get("sub")
                email = idinfo.get("email")
                name = idinfo.get("name", email.split("@")[0] if email else "Google User")
                avatar = idinfo.get("picture")
            except Exception as e:
                print(f"Google ID token verification failed: {e}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid Google ID token: {str(e)}"
                )
        
        if not google_id or not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Google payload - valid code or credential required"
            )
            
    from app.models.models import UserOAuthAccount
    oauth_acc = db.query(UserOAuthAccount).filter(
        UserOAuthAccount.provider == "google",
        UserOAuthAccount.provider_user_id == google_id
    ).first()
    
    if oauth_acc:
        user = oauth_acc.user
    else:
        user = db.query(User).filter(User.email == email).first()
    
    if not user:
        # Create a new user and attached Google OAuth account
        user = User(
            email=email,
            full_name=name,
            auth_provider="GOOGLE",
            is_active=True
        )
        db.add(user)
        db.flush()  # assign user.id
        
        oauth_acc = UserOAuthAccount(
            user_id=user.id,
            provider="google",
            provider_user_id=google_id,
            provider_email=email,
            provider_name=name,
            provider_avatar=avatar,
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            access_token=access_token,
            refresh_token=refresh_token,
            token_expiry=expiry
        )
        db.add(oauth_acc)
        db.commit()
        db.refresh(user)
    else:
        # Update existing user and user's Google OAuth account
        if user.auth_provider != "GOOGLE":
            user.auth_provider = "GOOGLE"

        if not oauth_acc:
            oauth_acc = user.google_account
            if not oauth_acc:
                oauth_acc = UserOAuthAccount(user_id=user.id, provider="google")
                db.add(oauth_acc)

        oauth_acc.provider_user_id = google_id
        oauth_acc.provider_email = email
        oauth_acc.provider_name = name
        if avatar:
            oauth_acc.provider_avatar = avatar
        if settings.GOOGLE_CLIENT_ID:
            oauth_acc.client_id = settings.GOOGLE_CLIENT_ID
        if settings.GOOGLE_CLIENT_SECRET:
            oauth_acc.client_secret = settings.GOOGLE_CLIENT_SECRET
        if access_token is not None:
            oauth_acc.access_token = access_token
        if refresh_token is not None:
            oauth_acc.refresh_token = refresh_token
        if expiry is not None:
            oauth_acc.token_expiry = expiry

        db.commit()
        db.refresh(user)
            
    # Auto-initialize user's Google Drive folder if logged in with Google and folder is not set
    if user.google_access_token and not user.google_drive_folder_id:
        try:
            from app.services.google_drive import drive_service
            drive_service._ensure_user_service(user.id, db)
            if drive_service.service:
                folder_id = drive_service.get_or_create_folder(drive_service.service)
                if folder_id:
                    user.google_drive_folder_id = folder_id
                    db.commit()
                    db.refresh(user)
        except Exception as folder_err:
            print(f"Failed to auto-create Google Drive folder on login: {folder_err}")

    jwt_token = create_access_token(subject=user.id)
    return {"access_token": jwt_token, "token_type": "bearer"}

@router.get("/google/callback")
def google_callback(code: str, state: Optional[str] = None):
    """
    Placeholder redirect callback.
    """
    return {"status": "success", "code": code}

@router.post("/google-drive/connect")
def connect_google_drive(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Connect user's Google Drive storage.
    """
    code = payload.get("code")
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authorization code is required."
        )
    
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth is not configured on the server."
        )
        
    try:
        from google_auth_oauthlib.flow import Flow
        from app.services.google_drive import drive_service
        import requests as http_requests
        
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=GOOGLE_SCOPES,
            redirect_uri="postmessage"
        )
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        # Save credentials to user record
        current_user.google_client_id = settings.GOOGLE_CLIENT_ID
        current_user.google_client_secret = settings.GOOGLE_CLIENT_SECRET
        current_user.google_access_token = credentials.token
        if credentials.refresh_token:
            current_user.google_refresh_token = credentials.refresh_token
        if hasattr(credentials, "expiry") and credentials.expiry:
            current_user.google_token_expiry = credentials.expiry
            
        # Get user details from API
        userinfo_url = "https://www.googleapis.com/oauth2/v3/userinfo"
        headers = {"Authorization": f"Bearer {credentials.token}"}
        userinfo_resp = http_requests.get(userinfo_url, headers=headers)
        if userinfo_resp.status_code == 200:
            userinfo = userinfo_resp.json()
            current_user.google_email = userinfo.get("email")
            current_user.google_name = userinfo.get("name")
            current_user.google_avatar = userinfo.get("picture")
            
        db.commit()
        db.refresh(current_user)
        
        # Initialize Google Drive service & auto-create the folder
        drive_service._ensure_user_service(current_user.id, db)
        if drive_service.service:
            folder_id = drive_service.get_or_create_folder(drive_service.service)
            if folder_id:
                current_user.google_drive_folder_id = folder_id
                db.commit()
                
        return {"status": "success", "message": "Google Drive connected successfully"}
    except Exception as e:
        print(f"Failed to connect Google Drive: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Google Drive connection failed: {str(e)}"
        )

@router.get("/google-drive/status")
def get_google_drive_status(
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve connection status of user's Google Drive.
    """
    connected = current_user.google_access_token is not None and current_user.google_refresh_token is not None
    return {
        "connected": connected,
        "google_email": current_user.google_email,
        "google_name": current_user.google_name,
        "google_avatar": current_user.google_avatar,
        "google_drive_folder_id": current_user.google_drive_folder_id
    }

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/profile", response_model=UserResponse)
def update_profile(
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if user_in.full_name is not None:
        current_user.full_name = user_in.full_name
    if user_in.password is not None and user_in.password.strip():
        current_user.hashed_password = get_password_hash(user_in.password)
    if user_in.google_client_id is not None:
        current_user.google_client_id = user_in.google_client_id
    if user_in.google_client_secret is not None:
        current_user.google_client_secret = user_in.google_client_secret
    if user_in.google_access_token is not None:
        if user_in.google_access_token == "":
            current_user.google_access_token = None
            current_user.google_refresh_token = None
            current_user.google_drive_folder_id = None
        else:
            current_user.google_access_token = user_in.google_access_token
    if user_in.google_refresh_token is not None:
        if user_in.google_refresh_token == "":
            current_user.google_refresh_token = None
        else:
            current_user.google_refresh_token = user_in.google_refresh_token
            
    # Handle google authorization code exchange to link drive automatically
    if user_in.google_auth_code:
        if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Google OAuth is not configured on the server."
            )
        try:
            from google_auth_oauthlib.flow import Flow
            from app.services.google_drive import drive_service
            import requests as http_requests
            
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": settings.GOOGLE_CLIENT_ID,
                        "client_secret": settings.GOOGLE_CLIENT_SECRET,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                    }
                },
                scopes=GOOGLE_SCOPES,
                redirect_uri="postmessage"
            )
            flow.fetch_token(code=user_in.google_auth_code)
            credentials = flow.credentials
            
            current_user.google_client_id = settings.GOOGLE_CLIENT_ID
            current_user.google_client_secret = settings.GOOGLE_CLIENT_SECRET
            current_user.google_access_token = credentials.token
            if credentials.refresh_token:
                current_user.google_refresh_token = credentials.refresh_token
            if hasattr(credentials, "expiry") and credentials.expiry:
                current_user.google_token_expiry = credentials.expiry
                
            # Get user info
            userinfo_url = "https://www.googleapis.com/oauth2/v3/userinfo"
            headers = {"Authorization": f"Bearer {credentials.token}"}
            userinfo_resp = http_requests.get(userinfo_url, headers=headers)
            if userinfo_resp.status_code == 200:
                userinfo = userinfo_resp.json()
                current_user.google_email = userinfo.get("email")
                current_user.google_name = userinfo.get("name")
                current_user.google_avatar = userinfo.get("picture")
                
            db.commit()
            db.refresh(current_user)
            
            # Initialise Drive service & create folder
            drive_service._ensure_user_service(current_user.id, db)
            if drive_service.service:
                folder_id = drive_service.get_or_create_folder(drive_service.service)
                if folder_id:
                    current_user.google_drive_folder_id = folder_id
                    
        except Exception as e:
            print(f"Failed to exchange google_auth_code during profile update: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Google code exchange failed: {str(e)}"
            )

    db.commit()
    db.refresh(current_user)
    return current_user
