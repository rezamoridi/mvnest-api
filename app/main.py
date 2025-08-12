import os
from dotenv import load_dotenv

import uvicorn

load_dotenv()
ENV = os.getenv("ENV", default="dev")



if __name__ == "__main__":
    uvicorn.run(
        "config:app",  # Point to the app object in config.py
        host="0.0.0.0",
        port=8000,
        reload=True if ENV == "dev" else False,
        log_config=None # Uvicorn will use the app's configured logging
    )

