from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class listParams(BaseModel):
    """获取用户信息的请求参数模型

    Attributes:
        method: 固定为 "list" 的请求方法标识
    """

    model_config = ConfigDict(extra="ignore")  # 忽略额外字段
    method: Literal["list"] = Field(default="list", description="固定值")
    dir: str = "/"
    order: Literal["name", "size", "time"] = "name"
    desc: Literal[0, 1] = 1
    start: int = 0
    limit: int = 100
    web: Literal[0, 1] = 0
    folder: Literal[0, 1] = 0
    showempty: Literal[0, 1] = 0


class listallParams(BaseModel):
    model_config = ConfigDict(extra="ignore")  # 忽略额外字段
    method: Literal["listall"] = Field(default="listall", description="固定值")

    path: str = "/"
    recursion: Literal[0, 1] = 0
    order: Literal["name", "size", "time"] = "name"
    desc: Literal[0, 1] = 0
    start: int = Field(default=0, ge=0)
    limit: int = Field(default=1000, ge=0)
    ctime: Optional[int] = None
    mtime: Optional[int] = None
    web: Literal[0, 1] = 0
    device_id: Optional[str] = None

    # 检查path,必须以/开头
    @field_validator("path")
    @classmethod
    def check_path(cls, v):
        if not v.startswith("/"):
            raise ValueError("path must start with /")
        return v
