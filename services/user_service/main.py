"""
User Service - Manages user data, preferences, and authentication
"""
from fastapi import FastAPI, HTTPException, Depends, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import EmailStr
from typing import Optional
import sys
import os

# Add shared directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from shared.models import ResponseModel, UserPreference, PaginationMeta
from shared.logger import get_logger, set_correlation_id, correlation_id
from database import get_db, init_db
from models import User, UserCreate, UserUpdate, UserResponse, LoginRequest, LoginResponse
from auth import verify_token, create_access_token, get_password_hash, verify_password
from dependencies import get_current_user

logger = get_logger(__name__)

app = FastAPI(
    title="User Service",
    description="User management and authentication service",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()


@app.middleware("http")
async def correlation_id_middleware(request, call_next):
    """Add correlation ID to requests"""
    cid = request.headers.get("X-Correlation-ID")
    set_correlation_id(cid)
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id.get() or 'no-id'
    return response


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_db()
    logger.info("User Service started")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "user_service"}


@app.post("/api/v1/users/", response_model=ResponseModel[UserResponse], status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """Create a new user"""
    try:
        # Check if user exists
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            return ResponseModel.error_response(
                error="User with this email already exists",
                message="User creation failed"
            )

        # Create user
        # Ensure password is a string and handle bcrypt 72-byte limit
        password = str(user_data.password) if user_data.password else ""
        if not password:
            return ResponseModel.error_response(
                error="Password is required",
                message="User creation failed"
            )
        
        # Hash the password (with bcrypt 72-byte limit handling)
        try:
            hashed_password = get_password_hash(password)
        except Exception as hash_error:
            logger.error(f"Password hashing error: {hash_error}")
            return ResponseModel.error_response(
                error=f"Password hashing failed: {str(hash_error)}",
                message="User creation failed"
            )
        
        db_user = User(
            name=user_data.name,
            email=user_data.email,
            password_hash=hashed_password,
            push_token=user_data.push_token,
            email_enabled=user_data.preferences.email,
            push_enabled=user_data.preferences.push
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        logger.info(f"User created: {db_user.id}")
        # Convert datetime fields to strings for Pydantic v2
        user_dict = {
            "id": str(db_user.id),
            "name": db_user.name,
            "email": db_user.email,
            "push_token": db_user.push_token,
            "email_enabled": db_user.email_enabled,
            "push_enabled": db_user.push_enabled,
            "created_at": db_user.created_at.isoformat() if db_user.created_at else None,
        }
        return ResponseModel.success_response(
            data=UserResponse.model_validate(user_dict),
            message="User created successfully"
        )
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        db.rollback()
        return ResponseModel.error_response(
            error=str(e),
            message="Failed to create user"
        )


@app.get("/api/v1/users/{user_id}", response_model=ResponseModel[UserResponse])
async def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user by ID"""
    try:
        db_user = db.query(User).filter(User.id == user_id).first()
        if not db_user:
            return ResponseModel.error_response(
                error="User not found",
                message="User retrieval failed"
            )

        # Users can only view their own data unless admin
        if str(current_user.id) != user_id:
            return ResponseModel.error_response(
                error="Unauthorized",
                message="Access denied"
            )

        # Convert datetime fields to strings for Pydantic v2
        user_dict = {
            "id": str(db_user.id),
            "name": db_user.name,
            "email": db_user.email,
            "push_token": db_user.push_token,
            "email_enabled": db_user.email_enabled,
            "push_enabled": db_user.push_enabled,
            "created_at": db_user.created_at.isoformat() if db_user.created_at else None,
        }
        return ResponseModel.success_response(
            data=UserResponse.model_validate(user_dict),
            message="User retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Error retrieving user: {e}")
        return ResponseModel.error_response(
            error=str(e),
            message="Failed to retrieve user"
        )


@app.put("/api/v1/users/{user_id}", response_model=ResponseModel[UserResponse])
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update user"""
    try:
        db_user = db.query(User).filter(User.id == user_id).first()
        if not db_user:
            return ResponseModel.error_response(
                error="User not found",
                message="User update failed"
            )

        # Users can only update their own data
        if str(current_user.id) != user_id:
            return ResponseModel.error_response(
                error="Unauthorized",
                message="Access denied"
            )

        # Update fields
        if user_data.name:
            db_user.name = user_data.name
        if user_data.push_token is not None:
            db_user.push_token = user_data.push_token
        if user_data.preferences:
            db_user.email_enabled = user_data.preferences.email
            db_user.push_enabled = user_data.preferences.push

        db.commit()
        db.refresh(db_user)

        logger.info(f"User updated: {user_id}")
        # Convert datetime fields to strings for Pydantic v2
        user_dict = {
            "id": str(db_user.id),
            "name": db_user.name,
            "email": db_user.email,
            "push_token": db_user.push_token,
            "email_enabled": db_user.email_enabled,
            "push_enabled": db_user.push_enabled,
            "created_at": db_user.created_at.isoformat() if db_user.created_at else None,
        }
        return ResponseModel.success_response(
            data=UserResponse.model_validate(user_dict),
            message="User updated successfully"
        )
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        db.rollback()
        return ResponseModel.error_response(
            error=str(e),
            message="Failed to update user"
        )


@app.post("/api/v1/users/login", response_model=ResponseModel[LoginResponse])
async def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    """User login"""
    try:
        user = db.query(User).filter(User.email == credentials.email).first()
        if not user or not verify_password(credentials.password, user.password_hash):
            return ResponseModel.error_response(
                error="Invalid email or password",
                message="Login failed"
            )

        token = create_access_token({"sub": str(user.id), "email": user.email})
        logger.info(f"User logged in: {user.id}")
        
        return ResponseModel.success_response(
            data=LoginResponse(access_token=token, token_type="bearer"),
            message="Login successful"
        )
    except Exception as e:
        logger.error(f"Error during login: {e}")
        return ResponseModel.error_response(
            error=str(e),
            message="Login failed"
        )


@app.get("/api/v1/users/{user_id}/preferences", response_model=ResponseModel[UserPreference])
async def get_preferences(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user preferences"""
    try:
        if str(current_user.id) != user_id:
            return ResponseModel.error_response(
                error="Unauthorized",
                message="Access denied"
            )

        db_user = db.query(User).filter(User.id == user_id).first()
        if not db_user:
            return ResponseModel.error_response(
                error="User not found",
                message="Failed to retrieve preferences"
            )

        preferences = UserPreference(
            email=db_user.email_enabled,
            push=db_user.push_enabled
        )

        return ResponseModel.success_response(
            data=preferences,
            message="Preferences retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Error retrieving preferences: {e}")
        return ResponseModel.error_response(
            error=str(e),
            message="Failed to retrieve preferences"
        )


@app.get("/internal/users/{user_id}", response_model=ResponseModel[UserResponse])
async def get_user_internal(
    user_id: str,
    db: Session = Depends(get_db),
    x_service_token: Optional[str] = Header(None, alias="X-Service-Token")
):
    """Internal endpoint for service-to-service calls (no user auth required)"""
    try:
        # Simple service token check (in production, use proper service authentication)
        service_token = os.getenv("SERVICE_TOKEN", "internal-service-token")
        if x_service_token != service_token:
            return ResponseModel.error_response(
                error="Unauthorized",
                message="Invalid service token"
            )

        db_user = db.query(User).filter(User.id == user_id).first()
        if not db_user:
            return ResponseModel.error_response(
                error="User not found",
                message="User retrieval failed"
            )

        # Convert datetime fields to strings for Pydantic v2
        user_dict = {
            "id": str(db_user.id),
            "name": db_user.name,
            "email": db_user.email,
            "push_token": db_user.push_token,
            "email_enabled": db_user.email_enabled,
            "push_enabled": db_user.push_enabled,
            "created_at": db_user.created_at.isoformat() if db_user.created_at else None,
        }
        return ResponseModel.success_response(
            data=UserResponse.model_validate(user_dict),
            message="User retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Error retrieving user: {e}")
        return ResponseModel.error_response(
            error=str(e),
            message="Failed to retrieve user"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

