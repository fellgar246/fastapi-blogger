import os
from datetime import datetime
from fastapi import FastAPI, HTTPException, Path, Query, status, Depends
from pydantic import BaseModel, Field, field_validator, EmailStr, ConfigDict
from typing import Optional, List, Union, Literal
from math import ceil
from sqlalchemy import create_engine, Integer, String, Text, DateTime, select, func, UniqueConstraint, ForeignKey, Table, Column
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase, Mapped, mapped_column, relationship, selectinload, joinedload
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from dotenv import load_dotenv

load_dotenv()


Base.metadata.create_all(bind=engine)


app = FastAPI(title="Mini Blog")


# BLOG_POSTS = [
#     {"id": 1, "title": "First Post",
#         "content": "This is the content of the first post."},
#     {"id": 2, "title": "Second Post",
#         "content": "This is the content of the second post.",
#         "tags": [{"name": "Python"}, {"name": "FastAPI"}]},
#     {"id": 3, "title": "Third Post",
#         "content": "This is the content of the third post."},
#     {"id": 4, "title": "Fourth Post",
#         "content": "This is the content of the fourth post.",
#         "author": {"name": "John Doe", "email": "john.doe@example.com"}},
#     {"id": 5, "title": "Fifth Post",
#         "content": "This is the content of the fifth post.",
#         "tags": [{"name": "Programming"}, {"name": "Tutorial"}],
#         "author": {"name": "Jane Smith", "email": "jane.smith   @example.com"}},
# ]


@app.get("/")
def home():
    return {"message": "Welcome to the Mini Blog!"}


@app.put("/posts/{post_id}", response_model=PostPublic, response_description="Post actualizado exitosamente", response_model_exclude=True)
def update_post(post_id: int, data: PostUpdate, db: Session = Depends(get_db)):

    post = db.get(PostORM, post_id)

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    updates = data.model_dump(exclude_unset=True)

    for key, value in updates.items():
        setattr(post, key, value)

    db.add(post)
    db.commit()
    db.refresh(post)

    raise post


@app.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(post_id: int, db: Session = Depends(get_db)):

    post = db.get(PostORM, post_id)

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    db.delete(post)
    db.commit()

    return
