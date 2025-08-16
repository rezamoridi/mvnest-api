
import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from dotenv import load_dotenv
import jwt
import bcrypt
from jwt.algorithms import get_default_algorithms
from jwt.exceptions import InvalidAlgorithmError



from schemas import schemas
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app_log_config import logger



# --- Configuration ---
# In a real application, load these from a .env file or other config source.
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))


def validate_jwt_algorithm_env() -> str:
    """
    Reads the JWT algorithm from environment and validates it.

    Returns:
        str: The validated algorithm.

    Raises:
        InvalidAlgorithmError: If the algorithm is not supported.
    """
    algo = os.getenv("ALGORITHM", "HS256")
    # Remove any surrounding quotes or whitespace
    algo = algo.strip().strip("'").strip('"')

    if algo not in get_default_algorithms():
        logger.critical(f"Invalid JWT algorithm from env: {algo}")
        raise InvalidAlgorithmError(f"Invalid JWT algorithm: {algo}")

    logger.info(f"JWT algorithm '{algo}' is valid.")
    return algo


# Reusable security scheme
# This creates the "Authorize" button in the Swagger UI
oauth2_scheme = HTTPBearer()

# --- JWT Token Functions ---



def create_access_token(sub: int, role: str, expires_delta: Optional[timedelta] = None):
    """
    Generate a JSON Web Token (JWT) access token with an optional expiration time.

    Args:
        data (schemas.Payload): The payload data to encode in the JWT.  
            Must include claims such as `sub` (subject/user ID) and `role`.
        expires_delta (Optional[timedelta], optional): The time duration after which the token expires.  
            If not provided, a default expiration should be applied inside the function.

    Returns:
        str: A JWT access token encoded as a URL-safe string.
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    try:
        # Convert Pydantic model to dict, update exp and type
        payload = {
            "sub": str(sub),
            "role": role,
            "exp": expire,
            "type": "access"
        }

        encoded_jwt = jwt.encode(payload=payload, key=SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    except Exception as e:
        logger.exception("Error in create access token happend: {e}")



# --- Authentication Dependency ---
async def get_current_user(token: HTTPAuthorizationCredentials=Depends(oauth2_scheme)) -> schemas.DecodeJWT:
    """
    Dependency to get the current user from a JWT token.

    This function is used in endpoint decorators to protect routes.
    It decodes the JWT, validates its signature and expiration,
    and fetches the user from the database.

    Args:
        token (HTTPAuthorizationCredentials): The bearer token from the request header.

    Raises:
        HTTPException: 401 Unauthorized if the token is invalid, expired,
                       or the user is not found.

    Returns:
        User: The authenticated user object.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # The token.credentials contains the actual JWT string
        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        sub: str = payload.get("sub")
        if sub is None:
            raise credentials_exception
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise credentials_exception
    
    return payload




async def get_current_admin(token: HTTPAuthorizationCredentials=Depends(oauth2_scheme)) -> schemas.DecodeJWT:
    """
    Dependency to get the current user from a JWT token.

    This function is used in endpoint decorators to protect routes.
    It decodes the JWT, validates its signature and expiration,
    and fetches the user from the database.

    Args:
        token (HTTPAuthorizationCredentials): The bearer token from the request header.

    Raises:
        HTTPException: 401 Unauthorized if the token is invalid, expired,
                       or the user is not found.

    Returns:
        User: The authenticated user object.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # The token.credentials contains the actual JWT string
        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        sub: str = payload.get("sub")
        role: str = payload.get("role")
        if sub is None:
            raise credentials_exception
        if role == "user":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acess Denied. need administration access privilages"               
            )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise credentials_exception
    
    return payload





class PwdHandler:
    """
    A utility class for handling password hashing and verification.

    This class provides static methods to securely hash new passwords and
    to check if a given plain-text password matches a previously
    hashed one. It uses bcrypt algorithm.
    """

    @staticmethod
    def hash_pwd(password: str) -> bytes:
        """
        Hashes a plain-text password using bcrypt.

        Args:
            password (str): The plain-text password to str.

        Returns:
            bytes: The resulting hashed password as bytes.
        """
        return bcrypt.hashpw(password=password.encode(), salt=bcrypt.gensalt()) 
    
    @staticmethod
    def check_pwd(password:str, hashed_pwd: bytes) -> bool:
        """
        Verifies a plain-text password against a hashed password.

        Args:
            password (str): The plain-text password to check.
            hashed_pwd (bytes): The hashed password from the database.

        Returns:
            bool: True if the passwords match, False otherwise.
        """
        return bcrypt.checkpw(password=password.encode(), hashed_password=hashed_pwd)
    


    

if __name__ == "__main__":
    pass