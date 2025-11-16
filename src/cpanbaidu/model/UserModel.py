from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class uinfoParams(BaseModel):
    """获取用户信息的请求参数模型

    Attributes:
        vip_version: VIP版本号，可选参数
        method: 固定为 "uinfo" 的请求方法标识
    """

    model_config = ConfigDict(extra="ignore")  # 忽略额外字段

    vip_version: str | None = Field(default=None, description="VIP版本号")
    method: Literal["uinfo"] = Field(default="uinfo", description="固定值")


class uinfoResponse(BaseModel):
    model_config = ConfigDict(extra="allow")  # 允许额外字段

    baidu_name: str
    netdisk_name: str
    avatar_url: str
    vip_type: int
    uk: int


class quotaResponse(BaseModel):
    model_config = ConfigDict(extra="allow")  # 允许额外字段

    total: int
    used: int
    free: int
    expire: bool
