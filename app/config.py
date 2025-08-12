import os
from dotenv import load_dotenv
import time
import uuid

#import fastapi 
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy.exc import OperationalError

# Import resources from other modules
from db import engine
from log_config import logger
from routers import health_router, auth_router, admin_router, user_router




# Load environment variables
load_dotenv()
APP_ENV = os.getenv("ENV", default="dev")

# Api lifespan config
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup and shutdown events.
    """
    logger.info("Application startup: Initializing resources...")
    logger.warning(f"Application Environment: {APP_ENV}")
    try:
        with engine.connect() as connection:
            logger.success("Database connection successful!")
        yield
    except OperationalError as e:
        logger.critical(f"Database connection failed during startup: {e}")
        # Optionally, you can raise the exception to stop the app
        # raise e
        yield # Still yield to allow uvicorn to handle the shutdown
    finally:
        logger.info("Application shutdown: Releasing resources...")
        engine.dispose()

# Create the FastAPI app instance with the configured lifespan
app = FastAPI(
    title= "Movienest API",
    root_path="/api",
    lifespan=lifespan,
    )


# --- Request Logging Middleware ---
@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    logger.info(f"rid={request_id} start request path={request.url.path} method={request.method}")
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = (time.time() - start_time) * 1000
    formatted_process_time = '{0:.2f}'.format(process_time)
    logger.info(f"rid={request_id} completed_in={formatted_process_time}ms status_code={response.status_code}")
    
    return response

# Add Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(router=auth_router.router, tags=["Auth"])
app.include_router(router=admin_router.router, tags=["Admin"])
app.include_router(router=user_router.router, tags=["User"])
app.include_router(router=health_router.router, tags=["Healt Check"])
