import os
from fastapi import FastAPI
from app.core.db import Base, engine
from dotenv import load_dotenv
from app.api.v1.posts.router import router as posts_router
from app.api.v1.auth.router import router as auth_router
from app.api.v1.uploads.router import router as uploads_router
from app.api.v1.tags.router import router as tags_router
from app.api.v1.categories.router import router as categories_router
from fastapi.staticfiles import StaticFiles

load_dotenv()

MEDIA_DIR = "app/media"


def create_app() -> FastAPI:
    app = FastAPI(title="Blog API", version="1.0.0",
                  swagger_ui_parameters={"persistAuthorization": True})

    Base.metadata.create_all(bind=engine)  # dev
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(posts_router)
    app.include_router(tags_router)
    app.include_router(uploads_router)
    app.include_router(categories_router)

    os.makedirs(MEDIA_DIR, exist_ok=True)
    app.mount("/media", StaticFiles(directory=MEDIA_DIR), name="media")

    return app


app = create_app()
