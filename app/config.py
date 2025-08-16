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
from app_log_config import logger
from routers import health_router, auth_router, admin_router, user_router
from middleware.auth_middleware import validate_jwt_algorithm_env, InvalidAlgorithmError



# Load environment variables
load_dotenv()
APP_ENV = os.getenv("ENV", default="dev")
ORIGINS = [o.strip() for o in os.getenv("ORIGINS", "").split(",") if o.strip()]

# Api lifespan config
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup and shutdown events.
    Critical startup errors are logged and sinks are flushed before exiting.
    """
    logger.info("Application startup: Initializing resources...")
    
    try:
        # Perform all critical startup tasks
        validate_jwt_algorithm_env()
        engine.connect().close() # A simple connection check
        logger.warning(f"Environment setup: {APP_ENV}")
        logger.success("All startup checks passed!")

    except (InvalidAlgorithmError, OperationalError) as e:
        # 1. Log the exception as you were doing
        logger.exception("A fatal error occurred during startup. The application will shut down.")
        
        # 2. Force Loguru to flush all sinks before the process terminates
        logger.shutdown() 
        
        # 3. Re-raise the exception to ensure the application stops
        raise e

    # If we get here, startup was successful
    yield

    # Shutdown code runs here
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
    allow_origins=ORIGINS,  # Adjust this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(router=auth_router.router, tags=["Auth"])
app.include_router(router=admin_router.router, tags=["Admin"])
app.include_router(router=user_router.router, tags=["User"])
app.include_router(router=health_router.router, tags=["Healt Check"])
