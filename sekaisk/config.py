from pydantic import BaseModel
from typing import ClassVar


class Config(BaseModel):
    user_id: ClassVar[str] = "" #userid
    admin: ClassVar[int] =  None #qqnum