import time
from typing import Any, Dict, Literal, Optional

from pydantic import validate_call
from ratelimit import limits, sleep_and_retry

from .Auth import Auth
from .File import File
from .model.Base import FileListBaiduResponseModel, UserInfoModel
from .utils.Logger import log
from .utils.md5 import decrypt_md5


class FileList:
    """封装文件列表相关操作"""

    def __init__(self, auth: Auth, userinfo: UserInfoModel | None = None) -> None:
        self.auth = auth
        self.userinfo = userinfo
        self.file = File(auth, userinfo)

    @sleep_and_retry
    @limits(calls=1, period=1)
    def _safe_listall(self, **kwargs) -> dict:
        """安全调用 list_files 方法，遵守速率限制"""
        try:
            respjson = self.file.listall(**kwargs)
            if not respjson or not isinstance(respjson, dict):
                raise ValueError("listall 返回非字典类型")
            return respjson
        except Exception as e:
            log.error(f"safe_listall 调用失败: {e}")
            raise ValueError("safe_listall 调用失败") from e

    @validate_call
    def get_file_list(
        self,
        path: str = "/",
        recursion: Literal[0, 1] = 0,
        order: Literal["name", "size", "time"] = "name",
        desc: Literal[0, 1] = 0,
        start: int = 0,
        limit: int = 100,
        ctime: Optional[int] = None,
        mtime: Optional[int] = None,
        web: Literal[0, 1] = 0,
        device_id: Optional[str] = None,
    ) -> dict:
        """
        获取指定目录的全部文件列表，自动处理翻页，返回所有条目，结构与百度网盘接口一致。

        如果要递归获取子目录文件，请设置 recursion 参数为1。

        Args:
            path: 目录名称绝对路径, 必须/开头；
            recursion: 是否递归,0为否, 1为是, 默认为0 当目录下存在文件夹，并想获取到文件夹下的子文件时，可以设置 recursion 参数为1，即可获取到更深目录层级的文件。
            order: 排序方式, 默认为name, 可选值为name, size, time
            desc: 是否降序, 0为升序, 1为降序, 默认为0
            start: 起始位置, 默认为0
            limit: 返回数量, 查询数目, 默认为1000
            ctime: 创建时间, 文件上传时间, 设置此参数, 表示只返回上传时间大于ctime的文件
            mtime: 修改时间, 文件修改时间, 设置此参数, 表示只返回修改时间大于mtime的文件
            web: 是否web模式, 默认为0,  为1时返回缩略图地址
            device_id: 设备ID, 硬件设备必传

        其他参数请参考API文档

        Returns:
            返回的文件列表, 包含文件名、文件大小、文件类型等信息
        """
        all_list = []
        has_more = True
        has_more_int = 0
        request_id = None
        cursor = start
        max_tries = 5
        tries = 0
        while has_more and tries < max_tries:
            params = {
                "path": path,
                "recursion": recursion,
                "order": order,
                "desc": desc,
                "start": cursor,
                "limit": limit,
                "ctime": ctime,
                "mtime": mtime,
                "web": web,
                "device_id": device_id,
            }
            try:
                respjson = self.file.listall(**params)
                if not respjson or not isinstance(respjson, dict):
                    log.error(f"listall 返回非字典类型: {respjson}")
                    tries += 1
                    time.sleep(2 * tries)
                    continue
                request_id = respjson.get("request_id", None)
                all_list.extend(respjson.get("list", []))
                has_more_int = respjson.get("has_more", 0)
                has_more = has_more_int == 1
                cursor = respjson.get("cursor", 0)

                tries = 0  # 成功后重置重试计数
            except Exception as e:
                log.error(f"获取文件列表异常: {e}")
                tries += 1
                time.sleep(2 * tries)
                continue
        if tries >= max_tries:
            log.error("获取文件列表失败，已达到最大重试次数")

        return {
            "errno": 0,
            "request_id": request_id,
            "guid": 0,
            "pagenum": (len(all_list) + limit - 1) // limit,
            "has_more": has_more_int,
            "total": len(all_list),
            "list": all_list,
        }

    @validate_call
    def toshare123(
        self,
        path: str = "/",
        recursion: Literal[0, 1] = 0,
        order: Literal["name", "size", "time"] = "name",
        desc: Literal[0, 1] = 0,
        start: int = 0,
        limit: int = 100,
        ctime: Optional[int] = None,
        mtime: Optional[int] = None,
        web: Literal[0, 1] = 0,
        device_id: Optional[str] = None,
    ) -> dict:
        """
        将文件列表数据转换为 share123 格式，方便导入到 share123 网站进行分享和管理。
        {
            "scriptVersion": "3.0.3",
            "exportVersion": "1.0",
            "usesBase62EtagsInExport": true,
            "commonPath": "",
            "totalFilesCount": 2,
            "totalSize": 169387721,
            "formattedTotalSize": "161.54 MB",
            "files": [
                {
                "etag": "2tX9mBeL0aCUxnKC0K58MO",
                "size": "93753917",
                "path": "aaaa.pdf"
                },
                {
                "etag": "2B88YL39QMvENOHRIdkFiY",
                "size": "75633804",
                "path": "newzscmm.tar.gz"
                }
            ]
            }
        """
        respjson = self.get_file_list(
            path=path, recursion=recursion, order=order, desc=desc, start=start, limit=limit, ctime=ctime, mtime=mtime, web=web, device_id=device_id
        )
        return self.toshare123_v2(respjson)

    def toshare123_v2(self, data: dict) -> dict:
        """
        将文件列表数据转换为 share123 格式，方便导入到 share123 网站进行分享和管理。
        """
        # 1. 检查输入的data是否包含必要的字段
        parsed = FileListBaiduResponseModel.model_validate(data)
        data = parsed.model_dump()

        datalist = [file for file in parsed.list if file.get("isdir", 1) == 0]
        total_size = sum(file.get("size", 0) for file in datalist)
        share123_data = {
            "scriptVersion": "3.0.3",
            "exportVersion": "1.0",
            "usesBase62EtagsInExport": True,
            "commonPath": "",
            "totalFilesCount": data.get("total", 0),
            "totalSize": total_size,
            "formattedTotalSize": self._format_size(total_size),
            "files": self._format_files_for_share123(datalist),
        }
        return share123_data

    def _format_size(self, size: float) -> str:
        """格式化文件大小为可读字符串"""
        size = float(size)
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"

    def _safe_decrypt_md5(self, md5str: str) -> str:
        """
        安全解密 MD5 字符串，防止异常中断, 如果解密失败则返回原始字符串
        """
        if len(md5str) != 32:
            return md5str
        try:
            return decrypt_md5(md5str)
        except Exception:
            return md5str

    def _format_files_for_share123(self, datalist: list[Dict[str, Any]]) -> list[dict]:
        """格式化文件列表为 share123 所需格式"""
        formatted_files = []

        for file in datalist:
            md5 = self._safe_decrypt_md5(file.get("md5", ""))

            if len(md5) != 32:
                continue

            formatted_file = {"etag": md5, "size": str(file.get("size", 0)), "path": file.get("path", "")}
            formatted_files.append(formatted_file)
        return formatted_files
