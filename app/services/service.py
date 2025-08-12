from datetime import datetime, timezone
from fastapi import HTTPException, status
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func, select

from schemas import schemas
from middleware.auth_middleware import create_access_token, PwdHandler
from log_config import logger
from models import models


class UserRepository:
    """
    Handles all synchronous database operations related to the User model.
    """
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_id(self, user_id) -> schemas.User:
        return self.db.query(models.User).filter(models.User.id == user_id).first()

    def get_by_username(self, username: str) -> Optional[models.User]:
        return self.db.query(models.User).filter(models.User.username == username).first()
    
    def get_by_email(self, email: str) -> Optional[models.User]:
        return self.db.query(models.User).filter(models.User.email == email).first()
    
    def get_users_count(self) -> int:
        return self.db.query(func.count(models.User.id)).scalar()
    
    def get_users(self, search: str | None = None, page: int = 1, page_size: int = 10):
        stmt = select(models.User)
        if search:
            like_pattern = f"%{search}%"
            stmt = stmt.where(
                (models.User.username.ilike(like_pattern)) |
                (models.User.email.ilike(like_pattern))
            )
        
        total_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.execute(total_stmt).scalar_one()

        # Apply pagination
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        results = self.db.execute(stmt).scalars().all()

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "results": results
        }
    
    def get_me(self, user_id: int):
        return self.db.query(models.User).filter(models.User.id == user_id).first()
                
    def create(self, user_create: schemas.UserCreate, hashed_password: str):
        db_user = models.User(
            username=user_create.username,
            email=user_create.email,
            password=hashed_password
        )
        self.db.add(db_user)
        return db_user  # no commit here
    
    def get_active_subscriptions(self):
        now = datetime.now(timezone.utc)
        active_subs = (
            self.db.query(models.UserSubscription)
            .filter(
                models.UserSubscription.is_active == True,
                models.UserSubscription.end_date > now
            )
            .all()
        )
        return active_subs

    def count_active_subscriptions(self) -> int:
        now = datetime.now(timezone.utc)
        count = self.db.query(func.count(models.UserSubscription.id)).filter(
                models.UserSubscription.is_active == True,
                models.UserSubscription.end_date > now
            ).scalar()
        return count
    
    




class MovieRepository:
    """
    Handle all database operations related to the movies model
    """
    def __init__(self, db:Session):
        self.db = db

    def get_movies(self, limit:  Optional[int] = None):# -> Optional[models.Movie]:
        if limit:
            return self.db.query(models.Movie).limit(limit=limit).all()
        else:
            return self.db.query(models.Movie).all()

    def get_movies_count(self) -> int:
        return self.db.query(func.count(models.Movie.id)).scalar()

    def get_movie_by_id(self, id: int) -> Optional[models.Movie]:
        return self.db.query(models.Movie).filter(models.Movie.id == id).first()

    def get_movies(self, search: Optional[str] = None, page: int = 1, page_size: int = 10):
        query = self.db.query(models.Movie)

        # Search by title (case-insensitive)
        if search:
            query = query.filter(func.lower(models.Movie.title).like(f"%{search.lower()}%"))

        total = query.count()
        movies = (
            query
            .order_by(models.Movie.title.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "results": movies
        }

    




class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def signup(self, user_create: schemas.UserCreate) -> schemas.User:
        logger.info(f"Attempting signup for username: {user_create.username}")

        try:
            existing_username = self.user_repo.get_by_username(user_create.username)
            if existing_username:
                logger.warning(f"Signup failed: username '{user_create.username}' already registered")
                raise HTTPException(status_code=409, detail="Username already registered")
            
            existing_email = self.user_repo.get_by_email(user_create.email)
            if existing_email:
                logger.warning(f"Signup failed: email '{user_create.email}' already registered")
                raise HTTPException(status_code=409, detail="Email already registered")
            
            hashed_pwd = PwdHandler.hash_pwd(user_create.password)
            new_user = self.user_repo.create(user_create, hashed_pwd)

            # Commit here so rollback can catch everything
            self.user_repo.db.commit()
            self.user_repo.db.refresh(new_user)

            logger.success(f"User '{new_user.username}' created successfully")
            return new_user

        except HTTPException:
            # Don't wrap HTTPExceptions, just rollback and re-raise
            self.user_repo.db.rollback()
            raise

        except Exception as e:
            self.user_repo.db.rollback()
            logger.exception(f"Unexpected error during signup: {e}")
            raise HTTPException(status_code=500, detail="Something bad happened")
            


    def login(self, username: str, password: str):
        logger.info(f"Login attempt for username: {username}")

        user = self.user_repo.get_by_username(username)
        if not user or not PwdHandler.check_pwd(password, user.password):
            logger.warning(f"Login failed for username: {username} due to invalid credentials")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        access_token = create_access_token(sub=str(user.id), role=user.role)
        logger.success(f"User '{username}' access token created successfully")
        return {"access_token": access_token, "token_type": "bearer"}

    def read_access_token(self, user_id):
        return self.user_repo.get_me(user_id=user_id)





class AdminService:
    """
    Handle all database operations related to the admin
    """
    def __init__(self, movie_repo: MovieRepository, user_repo: UserRepository):
        self.movie_repo = movie_repo
        self.user_repo = user_repo
    
    def get_overview_data(self):
        return {
            "users_count": self.user_repo.get_users_count(),
            "moives_count": self.movie_repo.get_movies_count(),
            "subs_count": self.user_repo.count_active_subscriptions()
        }

    def get_users(self, search: str | None = None, page: int = 1, page_size: int = 10):
        return self.user_repo.get_users(search=search, page=page, page_size=page_size)

    def update_user(self, user_id, username: str):
        user = self.user_repo.get_user_by_id(user_id)
        if not user:
            logger.info(f"Admin attempted to update user with ID {user_id}, but user was not found")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        elif user:
            user.username = username
            user.updated_at = datetime.now(timezone.utc)
            self.user_repo.db.commit()
            self.user_repo.db.refresh(user)
            logger.info(f"Admin updated user (id={user_id}) username to '{username}'")

            return user

    def delete_user(self, user_id: int):
        user = self.user_repo.get_user_by_id(user_id)
        if not user:
            logger.info(f"Admin attempted to delete user with ID {user_id}, but user was not found")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        if user.is_deleted:
            logger.info(f"Admin attempted to delete a user (ID: {user_id}) already marked as deleted")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="User is already deleted")
        if user.role == "admin":
            logger.info(f"Admin attempt to delete a admin with ID {user_id} stoped")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Deleting Admin Not Allowd")
        
        user.is_deleted = True
        user.updated_at = datetime.now(timezone.utc)
        self.user_repo.db.commit()
        self.user_repo.db.refresh(user)
        logger.warning(f"Admin attempt to delete a User with ID {user_id} executed!")

        return {"message": "user deleted"}
    
    def get_movies(self, search: Optional[str] = None, page: int = 1, page_size: int = 10):
        logger.info(f"Fetching movies with search='{search}', page={page}, page_size={page_size}")
        movies = self.movie_repo.get_movies(search, page, page_size)
        logger.info(f"Fetched {len(movies)} movies")
        return movies

    def create_movie(self, movie_in: schemas.MovieCreate) -> schemas.MovieOut:
        movie_data = movie_in.model_dump()
        if movie_data.get("cover_url") is not None:
            movie_data["cover_url"] = str(movie_data["cover_url"])  # convert for DB only

        movie = models.Movie(**movie_data)
        self.movie_repo.db.add(movie)
        try:
            self.movie_repo.db.commit()
            self.movie_repo.db.refresh(movie)
            logger.info(f"Movie '{movie.title}' created with id={movie.id}")
        except Exception as e:
            logger.error(f"Failed to create movie '{movie_in.title}': {e}", exc_info=True)
            self.movie_repo.db.rollback()
            raise
        return movie
    
    def delete_movie(self, movie_id: int):
        existing_movie = self.movie_repo.get_movie_by_id(movie_id)
        if not existing_movie:
            logger.info(f"Delete movie failed: Movie with id={movie_id} not found")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Movie with id {movie_id} not found")

        try:
            self.movie_repo.db.delete(existing_movie)
            self.movie_repo.db.commit()
            logger.warning(f"Movie with id={movie_id} deleted successfully")
        except Exception as e:
            self.movie_repo.db.rollback()
            logger.error(f"Failed to delete movie with id={movie_id}: {e}", exc_info=True)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete movie")

        return existing_movie