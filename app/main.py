from fastapi import FastAPI
from app.config import APP_NAME, DEBUG
from app.api import router

app = FastAPI(
    title=APP_NAME,
    debug=DEBUG
)

app.include_router(router)
