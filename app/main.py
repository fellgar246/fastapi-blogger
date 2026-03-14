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

post_tags = Table(
    "post_tags",
    Base.metadata,
    Column("post_id", ForeignKey(
        "posts.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)
)


class AthorORM(Base):
    __tablename__ = "authors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True)

    posts: Mapped[List["PostORM"]] = relationship(back_populates="author")


class TagORM(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)

    posts: Mapped[List["PostORM"]] = relationship(
        secondary=post_tags,
        back_populates="tags",
        lazy="selectin",
    )


class PostORM(Base):
    __tablename__ = "posts"
    __table_args__ = (UniqueConstraint("title", name="unique_post_title"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow)

    author_id: Mapped[Optional[int]] = mapped_column(ForeignKey("authors.id"))
    author: Mapped[Optional[AthorORM]] = relationship(back_populates="posts")

    tags: Mapped[List[TagORM]] = relationship(
        secondary=post_tags,
        back_populates="posts",
        lazy="selectin",
        passive_deletes=True
    )


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


class Tag(BaseModel):
    name: str = Field(..., min_length=2, max_length=30,
                      description="Nombre de la etiqueta")

    model_config = ConfigDict(from_attributes=True)


class Author(BaseModel):
    name: str
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)


class PostBase(BaseModel):
    title: str
    content: Optional[str] = "Content not available"
    tags: Optional[List[Tag]] = Field(default_factory=list)
    author: Optional[Author] = None

    model_config = ConfigDict(from_attributes=True)


class PostCreate(BaseModel):
    title: str = Field(
        ...,
        min_length=5,
        max_length=100,
        description="Title of the blog post",
        examples=["My First Blog Post", "A Day in the Life"]
    )
    content: Optional[str] = Field(
        default="Content not available",
        min_length=10,
        description="Content of the blog post",
        examples=["This is the content of my first blog post.",
                  "Today I went to the park..."]
    )
    tags: List[Tag] = Field(default_factory=list)
    author: Optional[Author] = None

    @field_validator("title")
    @classmethod
    def not_allowed_title(cls, value: str) -> str:
        forbidden_titles = ["Untitled", "No Title", "Lorem Ipsum"]
        if value in forbidden_titles:
            raise ValueError(f"The title '{value}' is not allowed.")
        return value


class PostUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=5, max_length=100)
    content: Optional[str] = None


class PostPublic(PostBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class PostSummary(BaseModel):
    id: int
    title: str

    model_config = ConfigDict(from_attributes=True)


class PaginatedPost(BaseModel):
    page: int
    per_page: int
    total: int
    total_pages: int
    has_prev: bool
    has_next: bool
    order_by: Literal["id", "title"]
    direction: Literal["asc", "desc"]
    search: Optional[str] = None
    items: List[PostPublic]


@app.get("/")
def home():
    return {"message": "Welcome to the Mini Blog!"}


@app.get("/posts", response_model=PaginatedPost)
def list_posts(text: Optional[str] = Query(
    default=None,
    deprecated=True,
    description="Parameter deprecated, use 'search' instead",
),
    query: Optional[str] = Query(
    default=None,
    description="Search query for blog posts",
    alias="search",
    min_length=3,
    max_length=50,
    pattern="^[a-zA-Z0-9 ]+$",
),
    per_page: int = Query(
    10, ge=1, le=50, description="Number of items to return per page(1-50)"
),
    page: int = Query(
    1, ge=1, description="Page number to return (>=1)"
),
    order_by: Literal["id", "title"] = Query(
        "id", description="Field to order the results by"
),
    direction: Literal["asc", "desc"] = Query(
        "asc", description="Direction to order the results"
),
    db: Session = Depends(get_db)
):

    results = select(PostORM)

    query = query or text

    if query:
        results = results.where(PostORM.title.ilike(f"%{query}%"))

    total = db.scalar(select(func.count()).select_from(
        results.subquery())) or 0
    total_pages = ceil(total / per_page) if total > 0 else 0

    current_page = 1 if total_pages == 0 else min(page, total_pages)

    if order_by == "id":
        order_col = PostORM.id
    else:
        order_col = func.lower(PostORM.title)

    results = results.order_by(
        order_col.asc() if direction == "asc" else order_col.desc())

    if total_pages == 0:
        items: List[PostORM] = []
    else:
        start = (current_page - 1) * per_page
        items = db.execute(results.limit(
            per_page).offset(start)).scalars().all()

    has_prev = current_page > 1
    has_next = current_page < total_pages if total_pages > 0 else False

    return PaginatedPost(
        page=current_page,
        per_page=per_page,
        total=total,
        total_pages=total_pages,
        has_prev=has_prev,
        has_next=has_next,
        order_by=order_by,
        direction=direction,
        search=query,
        items=items
    )


@app.get("/posts/by_tags", response_model=List[PostPublic])
def filter_by_tags(
    tags: List[str] = Query(
        ...,
        min_length=1,
        description="List of tags to filter posts by",
    ),
    db: Session = Depends(get_db)
):
    normalized_tags = [tag.strip().lower() for tag in tags if tag.strip()]

    if not normalized_tags:
        raise []

    post_list = (
        select(PostORM).options(
            selectinload(PostORM.tags),
            joinedload(PostORM.author)
        ).where(PostORM.tags.any(func.lower(TagORM.name).in_(normalized_tags)))
        .order_by(PostORM.id.asc())
    )

    posts = db.execute(post_list).scalars().all()

    return posts


@app.get("/posts/{post_id}", response_model=Union[PostPublic, PostSummary], response_description="Post encontrado")
def get_post(post_id: int = Path(
    ...,
    ge=1,
    title="ID del post",
    description="ID del post, debe ser mayor o igual a 1",
    example=1
), include_content: bool = Query(default=True, description="Include post content in the response"), db: Session = Depends(get_db)):

    post_find = select(PostORM).where(PostORM.id == post_id)
    post = db.execute(post_find).scalar_one_or_none()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if include_content:
        return PostPublic.model_validate(post, from_attributes=True)

    return PostSummary.model_validate(post, from_attributes=True)


@app.post("/posts", response_model=PostPublic, response_description="Post creado exitosamente", status_code=status.HTTP_201_CREATED)
def create_post(post: PostCreate, db: Session = Depends(get_db)):
    author_obj = None
    if post.author:
        author_obj = db.execute(select(AthorORM).where(
            AthorORM.email == post.author.email)).scalar_one_or_none()

        if not author_obj:
            author_obj = AthorORM(name=post.author.name,
                                  email=post.author.email)
            db.add(author_obj)
            db.flush()

    new_post = PostORM(
        title=post.title, content=post.content, author=author_obj)

    for tag in post.tags:
        tag_obj = db.execute(select(TagORM).where(
            func.lower(TagORM.name) == tag.name.lower())).scalar_one_or_none()

        if not tag_obj:
            tag_obj = TagORM(name=tag.name)
            db.add(tag_obj)
            db.flush()

        new_post.tags.append(tag_obj)

    try:
        db.add(new_post)
        db.commit()
        db.refresh(new_post)
        return new_post
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="Post with this title already exists")
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error creating post")


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
