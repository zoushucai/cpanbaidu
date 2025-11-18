from typing import Any

from pydantic import BaseModel, ConfigDict, model_validator


class UserInfoModel(BaseModel):
    username: str
    userid: str
    isvip: bool | None = None
    viptype: int | None = None
    # 统一的用户模型
    # 过滤掉其他不必要的字段
    model_config = ConfigDict(extra="ignore")  # ✅ 忽略所有未定义字段


class AuthError(Exception):
    """百度 平台统一异常"""

    def __init__(self, code: int, message: str, detail: dict | None = None):
        self.code = code
        self.message = message
        self.detail = detail or {}
        super().__init__(f"[{code}] {message}")


class BaseResponse(BaseModel):
    """统一响应模型, 有些响应不含errmsg字段或request_id字段"""

    model_config = ConfigDict(extra="allow")  # ✅ 保留所有未定义字段

    errno: int
    request_id: str | int | None = None  # 某些接口可能不返回 request_id
    errmsg: str | None = None

    @model_validator(mode="after")
    def check_state(self) -> "BaseResponse":
        """验证 state 字段，失败时抛出 AuthError"""
        if self.errno != 0:
            raise AuthError(self.errno, self.errmsg or "未知错误")
        return self
