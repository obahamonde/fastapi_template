from pydantic import BaseModel, HttpUrl, EmailStr, Field, BaseConfig
from fastapi import UploadFile, File
from typing import Optional, List, Dict, Union, Callable
from src.utils import id, avatar, now
from faunadb.objects import Ref

class User(BaseModel):
    id: str = Field(default_factory=id)
    name : Optional[str] = Field()
    email: Optional[EmailStr] = Field()
    picture: Optional[Union[HttpUrl,str]] = Field(default_factory=avatar)