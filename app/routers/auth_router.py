from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.exceptions import ResponseValidationError

from sqlalchemy.orm import Session
from schemas import schemas
from db import get_db
from services.service import AuthService, UserRepository
from schemas.responses import COMMON_ERROR_RESPONSES



# --- Router Config ----
router = APIRouter(
    prefix="/auth"
)


# Dependency to provide AuthService instance
def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    user_repo = UserRepository(db)
    return AuthService(user_repo)


# --- Routers ---
@router.post("/signup", status_code=status.HTTP_201_CREATED, responses={**COMMON_ERROR_RESPONSES})
def signup(user_create: schemas.UserCreate, auth_service: AuthService = Depends(get_auth_service)) -> schemas.UserCreateResponse:
    new_user = auth_service.signup(user_create)
    return {
        "message": "User created successfully",
        "detail": {
            "id": new_user.id,
            "username": new_user.username,
            "email": new_user.email
        }
    }


@router.post("/login")
def login(user_login: schemas.UserLogin, auth_service: AuthService = Depends(get_auth_service)):
    token_response = auth_service.login(username=user_login.username, password=user_login.password)
    return token_response

