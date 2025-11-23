import re
from typing import Any, Dict

from pydantic import BaseModel, ConfigDict, Field, model_validator


def is_valid_md5(md5_str: str) -> bool:
    """检查字符串是否是有效的32位MD5哈希值"""
    return bool(re.match(r"^[a-f0-9]{32}$", md5_str.lower()))


class FileListBaiduResponseModel(BaseModel):
    model_config = ConfigDict(extra="allow")  # ✅ 保留所有未定义字段
    errno: int | None = Field(default=None, exclude=True)
    request_id: str | None = Field(default=None, exclude=True)
    list: list[Dict[str, Any]]

    # 且list中必须 有 isdir 字段
    @model_validator(mode="after")
    def check_state(self) -> "FileListBaiduResponseModel":
        """验证 list 的每个项是否包含 isdir 字段，失败时抛出 AuthError
        如果为空, 也通过验证
        """
        for item in self.list:
            if "isdir" not in item:
                raise ValueError("list 中的项缺少 isdir 字段")
        return self


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


class Share123FileModel(BaseModel):
    model_config = ConfigDict(extra="ignore")  # ✅ 忽略所有未定义字段
    etag: str
    size: str
    path: str

    @model_validator(mode="after")
    def normalize_path(self) -> "Share123FileModel":
        """确保etag 是32位的md5值"""
        if not is_valid_md5(self.etag):
            raise AuthError(1001, "etag 不是有效的32位MD5值")
        return self
