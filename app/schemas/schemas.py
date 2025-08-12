import re
from datetime import datetime
from typing import Optional, List, Annotated

from pydantic import BaseModel, Field, field_validator, EmailStr, AfterValidator, HttpUrl




def validate_username_format(value: str) -> str:
    """
    Checks the username against a single regex for format, length, and allowed characters.
    This one regex handles the starting character, allowed characters, and length (4-25 chars).
    """
    if not re.fullmatch(r"^[a-zA-Z][a-zA-Z0-9_]{3,24}$", value):
        raise ValueError(
            "Username must be 4-25 characters, start with a letter, and contain only letters, numbers, or underscores."
        )
    return value

def validate_password_complexity(value: str) -> str:
    """
    Validates that the password contains at least one uppercase letter,
    one lowercase letter, one digit, and one special character.
    """
    if not re.search(r"[A-Z]", value):
        raise ValueError("Password must contain at least one uppercase letter.")
    if not re.search(r"[a-z]", value):
        raise ValueError("Password must contain at least one lowercase letter.")
    if not re.search(r"\d", value):
        raise ValueError("Password must contain at least one digit.")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", value):
        raise ValueError("Password must contain at least one special character.")
    return value

# --- Step 2: Create Annotated Types ---
# Now, we create new, self-validating types using the functions above.

ValidatedUsername = Annotated[
    str,
    # Pydantic's own length validation runs first
    Field(min_length=4, max_length=25),
    # Our custom function runs after
    AfterValidator(validate_username_format),
]

ValidatedPassword = Annotated[
    str,
    Field(min_length=8, max_length=100),
    AfterValidator(validate_password_complexity),
]



# JWT Payload schema
class Payload(BaseModel):
    sub: int
    role: str
    exp: datetime
    type: str


class DecodeJWT(Payload):
    pass




# --- User Model ---

class UserCreate(BaseModel):
    username: ValidatedUsername
    email: EmailStr
    password: ValidatedPassword


class UserCreateDetail(BaseModel):
    id: int
    username: ValidatedUsername
    email: EmailStr



class User(UserCreate):
    id: int
    role: str
    access_token: str
    user_sub: str
    is_deleted: bool
    created_at: datetime
    updated_at: datetime


class UserLogin(BaseModel):
    username: ValidatedUsername
    password: ValidatedPassword



class UserUpdate(BaseModel):
    username: ValidatedUsername





# --- movie models ---

class MovieBase(BaseModel):
    title: str = Field(..., example="Inception")
    time: Optional[int] = Field(None, example=148, description="Duration in minutes")
    price: Optional[float] = Field(None, example=12.99)
    description: Optional[str] = Field(None, example="A mind-bending thriller by Christopher Nolan")
    imdb_rate: Optional[float] = Field(None, ge=0, le=10, example=8.8)
    cover_url: Optional[HttpUrl] = Field(None, example="https://example.com/inception.jpg")
    genre: Optional[str] = Field(None, example="Sci-Fi")

# Create schema
class MovieCreate(MovieBase):
    pass


# Update schema
class MovieUpdate(BaseModel):
    title: Optional[str] = None
    time: Optional[int] = None
    price: Optional[float] = None
    description: Optional[str] = None
    imdb_rate: Optional[float] = Field(None, ge=0, le=10)
    cover_url: Optional[HttpUrl] = None
    genre: Optional[str] = None


# Response schema
class MovieOut(MovieBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True



# --- Router Response ---

class Response(BaseModel):
    message: str
    detail: dict


class UserCreateResponse(Response):
    detail: UserCreateDetail


class DashboardOverview(BaseModel):
    users_count: int
    moives_count: int
    subs_count: int


# class UserPaginatedList(BaseModel):
#     users = List[User]