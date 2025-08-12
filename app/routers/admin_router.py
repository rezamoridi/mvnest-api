from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from fastapi.exceptions import ResponseValidationError

from sqlalchemy.orm import Session
from schemas import schemas
from db import get_db
from services.service import AuthService, UserRepository, AdminService, MovieRepository
from middleware.auth_middleware import get_current_user, get_current_admin
from schemas.responses import COMMON_ERROR_RESPONSES



# --- Router init ---
router = APIRouter(
    prefix="/admin",
    dependencies=[Depends(get_current_admin)]
)


# --- Router Dependency to provide AdminService instance ---
def admin_service(db: Session = Depends(get_db)) -> AdminService:
    user_repo = UserRepository(db)
    movie_repo = MovieRepository(db)
    return AdminService(movie_repo=movie_repo, user_repo=user_repo)

def auth_service(db: Session = Depends(get_db)) -> AuthService:
    user_repo = UserRepository(db)
    return AuthService(user_repo=user_repo)

# --- 1. Current admin info ---

@router.get(
    "/get_me",
    summary= "Reads Current Admin info"
)
def read_current_admin(
    service: AuthService = Depends(auth_service),
    user_credentials : str = Depends(get_current_admin)    
):
    return service.read_access_token(user_credentials["sub"])



# --- 2. Dashboard Overview Endpoint ---

@router.get(
    "/dashboard/overview",
    summary="Get summary data for the admin dashboard"
)
def get_dashboard_overview(service: AdminService = Depends(admin_service)):
    """
    Provides aggregated counts for the main dashboard widgets in a single call.
    """
    # Correct: Calling the method on the 'service' instance
    return service.get_overview_data()


# --- 3. User Management Endpoints ---

@router.get(
    "/users",
    summary="Get a paginated list of users"
)
def get_all_users(
    search: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    service: AdminService = Depends(admin_service)
):
    """
    Fetches a paginated and searchable list of all users.
    """
    return service.get_users(search=search, page=page, page_size=page_size)


@router.put(
    "/users/{user_id}",
    response_model= None,
    summary="Update a user's details"
)
def update_user_details(
    update_data: schemas.UserUpdate,
    service: AdminService = Depends(admin_service),
    user_id: int = Path(ge=1),
):
    """
    Updates a user's role or active status.
    """
    return service.update_user(user_id, update_data.username)



@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a user"
)
def delete_user_by_id(
    user_id: int,
    service: AdminService = Depends(admin_service)
):
    """
    Deletes a user from the database.
    """
    return service.delete_user(user_id=user_id)


# # --- 3. Movie Management Endpoints ---

@router.get(
    "/movies",
    response_model=None,
    summary="Get a paginated list of movies"
)
def get_all_movies(
    search: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    service: AdminService = Depends(admin_service)
):
    """
    Fetches a paginated and searchable list of all movies.
    """
    return service.get_movies(search, page, page_size)



@router.post(
    "/movies/create",
    response_model= schemas.MovieOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new movie"
)
def create_movie(
    movie_in: schemas.MovieCreate,
    service: AdminService = Depends(admin_service),
):
    """
    Creates a new movie in the database.
    """
    return service.create_movie(movie_in)



# @router.put(
#     "/movies/{movie_id}",
#     response_model=movie_schemas.MovieInDB,
#     summary="Update a movie's details"
# )
# def update_movie_details(movie_id: int, movie_update: movie_schemas.MovieUpdate, db: Session = Depends(get_db)):
#     """
#     Updates the details of an existing movie.
#     """
#     return admin_service.update_movie(db, movie_id=movie_id, movie_update=movie_update)

@router.delete(
    "/movies/{movie_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a movie by ID",
    responses={404: {"description": "Movie not found"}}
)
def delete_movie_route(
    movie_id: int = Path(..., ge=1),
    service: AdminService = Depends(admin_service)
):
    """
    Deletes a movie by its ID.
    """
    return service.delete_movie(movie_id)


# # --- 4. Admin Profile Management Endpoints ---
# # These would typically live in a separate `users_router.py` but are included here for completeness.

# @router.get(
#     "/me",
#     response_model=user_schemas.UserInDB,
#     summary="Get current admin profile"
# )
# def get_current_admin_profile(current_user: user_schemas.UserInDB = Depends(get_current_admin_user)):
#     """
#     Fetches the profile information of the currently authenticated admin.
#     """
#     return current_user

# @router.put(
#     "/me",
#     response_model=user_schemas.UserInDB,
#     summary="Update current admin profile"
# )
# def update_current_admin_profile(
#     user_update: user_schemas.AdminProfileUpdate,
#     db: Session = Depends(get_db),
#     current_user: user_schemas.UserInDB = Depends(get_current_admin_user)
# ):
#     """
#     Updates the username, email, or password of the currently authenticated admin.
#     """
#     return admin_service.update_profile(db, user_id=current_user.id, user_update=user_update)
