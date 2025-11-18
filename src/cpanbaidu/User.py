from typing import Literal

from pydantic import validate_call

from .Auth import Auth
from .model.Base import UserInfoModel
from .model.UserModel import uinfoParams, uinfoResponse
from .utils.Constants import API


class User:
    """
    用户信息类, 用于获取用户空间与 VIP 信息
    """

    def __init__(self, auth: Auth):
        """用户信息类初始化

        Args:
            auth: Auth 类实例

        """
        self.auth = auth
        self._user_resp_cache = None
        self.userinfo: UserInfoModel = self._fetch_user_info()

    def uinfo(self, vip_version: str | None = None) -> dict:
        """获取用户信息

        本接口用于获取用户的基本信息, 包括账号、头像地址、会员类型等.


        对应百度的API接口: [https://pan.baidu.com/union/doc/pksg0s9ns](https://pan.baidu.com/union/doc/pksg0s9ns)

        Args:
            vip_version (str | None): 可选的 VIP 版本号参数

        Returns:
            包含用户信息的字典
        """

        if self._user_resp_cache is not None:
            return self._user_resp_cache

        params_model = uinfoParams(vip_version=vip_version)
        params = params_model.model_dump(exclude_none=True)  # 仅包含非 None 字段
        respjson = self.auth.request_json("GET", API.UserPath.USER_INFO, params=params)
        parsed = uinfoResponse.model_validate(respjson)

        self._user_resp_cache = uinfoResponse.model_dump(parsed)
        return respjson

    def _fetch_user_info(self) -> UserInfoModel:
        """获取并缓存用户信息

        Returns:
            UserInfoModel: 用户信息模型

        Example Response:
            {'errno': 0, 'errmsg': 'succ', ....'baidu_name': '****', 'netdisk_name': 'ksk0001', 'uk': 11111, 'vip_type': 2}
        """
        try:
            resp = self.uinfo()
        except Exception as e:
            raise ValueError("无法获取用户信息") from e

        try:
            username = resp.get("baidu_name") or "未知用户"
            userid = str(resp.get("uk") or "0")
            vip_type = resp.get("vip_type", 0)
            isvip = vip_type > 0
            userinfo = UserInfoModel(
                username=username,
                userid=userid,
                isvip=isvip,
                viptype=vip_type,
            )
            return userinfo
        except Exception as e:
            print(f"获取用户信息失败: {e}")
            print(f"原始响应: {resp}")
            raise ValueError(f"解析用户信息失败: {e}") from e

    @validate_call
    def quota(
        self,
        checkfree: Literal[0, 1] = 0,
        checkexpire: Literal[0, 1] = 0,
    ) -> dict:
        """获取网盘容量信息

        本接口用于获取用户的网盘空间的使用情况, 包括总空间大小, 已用空间和剩余可用空间情况.

        对应百度的API接口: [https://pan.baidu.com/union/doc/Cksg0s9ic](https://pan.baidu.com/union/doc/Cksg0s9ic)

        Args:
            checkfree: 是否检查免费信息, 0为不查, 1为查, 默认为0
            checkexpire: 是否检查过期信息, 0为不查, 1为查, 默认为0

        Returns:
            包含网盘容量信息的字典
        """
        params = {
            "checkfree": checkfree,
            "checkexpire": checkexpire,
        }
        respjson = self.auth.request_json("GET", API.UserPath.QUOTA, params=params)
        # parsed = quotaResponse.model_validate(respjson)
        return respjson
