from fastapi import APIRouter,Depends

from services.service import AuthService, UserRepository
from middleware.auth_middleware import get_current_user
from db import get_db, Session




# --- Router Config ---
router = APIRouter(
    prefix="/user"
)

def auth_service(db: Session = Depends(get_db)) -> AuthService:
    user_repo = UserRepository(db)
    return AuthService(user_repo=user_repo)

# --- routers ---

@router.get(
    "/me",
    response_model=None
)
def get_me(
    service: AuthService=Depends(auth_service), 
    user_credentials: str = Depends(get_current_user)
):
    return service.read_access_token(user_credentials["sub"])


