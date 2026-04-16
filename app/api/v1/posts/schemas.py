from pydantic import BaseModel, Field, field_validator, EmailStr, ConfigDict
from typing import Optional, List, Union, Literal, Annotated
from fastapi import Form

from app.api.v1.auth.schemas import UserPublic
from app.api.v1.categories.schemas import CategoryPublic


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
    user: Optional[UserPublic] = None
    image_url: Optional[str] = None
    category: Optional[CategoryPublic] = None

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
    category_id: Optional[int] = None
    tags: List[Tag] = Field(default_factory=list)
    # author: Optional[Author] = None

    @field_validator("title")
    @classmethod
    def not_allowed_title(cls, value: str) -> str:
        forbidden_titles = ["Untitled", "No Title", "Lorem Ipsum"]
        if value in forbidden_titles:
            raise ValueError(f"The title '{value}' is not allowed.")
        return value

    @classmethod
    def as_form(
        cls,
        title: Annotated[str, Form(min_length=3)],
        content: Annotated[str, Form(min_length=10)],
        category_id: Annotated[int, Form(ge=1)],
        tags: Annotated[Optional[List[str]], Form()] = None,
    ):
        tag_objs = [Tag(name=t) for t in (tags or [])]
        return cls(title=title, content=content, category_id=category_id, tags=tag_objs)


class PostUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=5, max_length=100)
    content: Optional[str] = None


class PostPublic(PostBase):
    id: int
    slug: str
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
