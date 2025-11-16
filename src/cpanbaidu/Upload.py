import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock
from typing import Any, Literal, Optional

from pydantic import validate_call
from .model.Base import UserInfoModel
from .Auth import Auth
from .utils.Constants import API
from .utils.md5 import (
    calculate_md5,
    calculate_slice_md5,
    get_file_md5_blocks,
)


class Upload:
    def __init__(self, auth: Auth):
        """上传类
        
        Args:
            auth: Auth 类实例
        """
        self.auth = auth

    @validate_call
    def precreate(
        self,
        path: str,
        size: int,
        isdir: Literal[0, 1],
        block_list: list[str] | str,
        rtype: Literal[1, 2, 3] = 1,
        uploadid: Optional[str] = None,
        content_md5: Optional[str] = None,
        slice_md5: Optional[str] = None,
        local_ctime: Optional[int] = None,
        local_mtime: Optional[int] = None,
    ) -> dict[str, Any] | None:
        """预上传

        预上传是通知网盘云端新建一个上传任务, 网盘云端返回唯一ID uploadid 来标识此上传任务.

        对应百度的API接口: [https://pan.baidu.com/union/doc/3ksg0s9r7](https://pan.baidu.com/union/doc/3ksg0s9r7)

        注意事项:
            执行示例代码时，请将示例代码中的access_token参数值替换为自行获取的access_token
            云端文件重命名策略说明：当云端已有文件test.txt时，新的文件名字为test(1).txt；当云端已有目录 /dir时，新的目录名字为/dir(1)

        Args:
            path: 上传的文件或目录的路径
            size: 文件和目录两种情况:上传文件时, 表示文件的大小, 单位B；上传目录时, 表示目录的大小, 目录的话大小默认为0
            isdir: 是否为目录, 0 文件, 1 目录
            block_list: 分片上传时, 分片列表, 分片大小为4MB, 最大支持10000个分片
            rtype: 文件命名策略. 1 表示当path冲突时, 进行重命名 //2 表示当path冲突且block_list不同时, 进行重命名
            uploadid: 上传ID
            content_md5: 文件MD5, 32位小写
            slice_md5: 文件校验段的MD5, 32位小写, 校验段对应文件前256KB
            local_ctime: 客户端创建时间,  默认为当前时间戳
            local_mtime: 客户端修改时间,  默认为当前时间戳
        """
        # URL 参数：只有 method
        url_params = {
            "method": "precreate",
        }

        # RequestBody 参数：其他所有参数
        data = {
            "path": path,
            "size": size,
            "isdir": isdir,
            "block_list": json.dumps(block_list, separators=(",", ":")),
            "autoinit": 1,  # 固定值
            "rtype": rtype,
            "uploadid": uploadid,
            "content-md5": content_md5,
            "slice-md5": slice_md5,
            "local_ctime": local_ctime,
            "local_mtime": local_mtime,
        }

        respjson = self.auth.request_json("POST", API.UploadPath.PRECREATE, params=url_params, data=data)
        return respjson

    @validate_call
    def upload_part(self, url: str, path: str, uploadid: str, partseq: int, files: Any) -> dict[str, Any] | None:
        """分片上传
        本接口用于将本地文件上传到网盘云端服务器.


        文件分两种类型:小文件, 是指文件大小小于等于4MB的文件, 成功调用一次本接口后, 表示分片上传阶段完成；大文件, 是指文件大小大于4MB的文件, 需要先将文件按照4MB大小进行切分, 然后针对切分后的分片列表, 逐个分片进行上传, 分片列表的分片全部成功上传后, 表示分片上传阶段完成.

        根据不同的用户等级有不同的限制

        对应百度的API接口: [https://pan.baidu.com/union/doc/nksg0s9vi](https://pan.baidu.com/union/doc/nksg0s9vi)

        Args:
            url: 上传域名（从 locateupload 接口获取）
            path: 上传的文件的路径
            uploadid: 上传ID
            partseq: 分片序号, 从0开始
            files: 上传的文件内容

        Returns:
            分片上传结果
        """

        params = {
            "method": "upload",
            "type": "tmpfile",
            "path": path,
            "uploadid": uploadid,
            "partseq": partseq,
        }

        resp = self.auth.request("POST", url, params=params, files=files)
        return resp.json()

    @validate_call
    def create(
        self,
        path: str,
        size: str,
        isdir: Literal["0", "1"],
        block_list: list[str] | str,
        uploadid: str,
        rtype: Literal[1, 2, 3] = 1,
        local_ctime: Optional[int] = None,
        local_mtime: Optional[int] = None,
        zip_quality: Optional[Literal[50, 70, 100]] = None,
        zip_sign: Optional[int] = None,
        is_revision: Optional[int] = 0,
        mode: Optional[Literal[0, 1, 2, 3, 4, 5]] = None,
        exif_info: Optional[str] = None,
    ) -> dict[str, Any] | None:
        """创建文件

        本接口用于将多个文件分片合并成一个文件, 生成文件基本信息, 完成文件的上传最后一步.


        对应百度的API接口: [https://pan.baidu.com/union/doc/rksg0sa17](https://pan.baidu.com/union/doc/rksg0sa17)

        Args:
            path (str): 上传的文件或目录的路径
            size (str): 文件和目录两种情况:上传文件时, 表示文件的大小, 单位B；上传目录时, 表示目录的大小, 目录的话大小默认为0
            isdir (Literal[0, 1]): 是否为目录, 0 文件, 1 目录
            block_list (list[str] | str):  文件各分片md5数组的json串
            uploadid (str): 预上传precreate接口下发的uploadid
            rtype (Literal[1, 2, 3]): 文件命名策略.

                - 1 表示当path冲突时, 进行重命名
                - 2 表示当path冲突且block_list不同时, 进行重命名
                - 3 为覆盖, 需要与预上传precreate接口中的rtype保持一致
            local_ctime (Optional[int]): 客户端创建时间,  默认为当前时间戳
            local_mtime (Optional[int]): 客户端修改时间,  默认为当前时间戳
            zip_quality (Optional[Literal[50, 70, 100]]): 图片压缩程度, 有效值50、70、100, (与zip_sign一起使用)
            zip_sign (Optional[int]): 未压缩原始图片文件真实md5(与zip_quality一起使用)
            is_revision (Optional[int]): 是否需要多版本支持, 1为支持, 0为不支持,  默认为0 (带此参数会忽略重命名策略)
            mode (Optional[Literal[0, 1, 2, 3, 4, 5]]): 上传方式

                - 1 手动、
                - 2 批量上传
                - 3 文件自动备份
                - 4 相册自动备份
                - 5 视频自动备份
            exif_info (Optional[str]): json字符串, orientation、width、height、recovery为必传字段, 其他字段如果没有可以不传
        """
        # URL 参数：只有 method
        params = {
            "method": "create",
        }

        # RequestBody 参数：其他所有参数
        data = {
            "path": path,
            "size": size,
            "isdir": isdir,
            "block_list": block_list,
            "uploadid": uploadid,
            "rtype": rtype,
            "local_ctime": local_ctime,
            "local_mtime": local_mtime,
            "zip_quality": zip_quality,
            "zip_sign": zip_sign,
            "is_revision": is_revision,
            "mode": mode,
            "exif_info": exif_info,
        }
        respjson = self.auth.request_json("POST", API.UploadPath.CREATE, params=params, data=data)
        return respjson

    @validate_call
    def upload_simple(
        self,
        url: str,
        path: str,
        file: Any,
        ondup: Literal["newcopy", "overwrite", "fail"] = "newcopy",
    ) -> dict[str, Any] | None:
        """简单上传文件

        本接口用于将本地小文件上传到网盘云端服务器.


        对应百度的API接口: [https://pan.baidu.com/union/doc/Llvw5hfnm](https://pan.baidu.com/union/doc/Llvw5hfnm)

        Args:
            url: 上传域名（从 locateupload 接口获取）
            path: 上传的文件绝对路径
            ondup: 文件冲突处理策略, 上传的文件绝对路径冲突时的策略。

                - fail: 直接返回失败(默认, 改成 newcopy)
                - newcopy: 重命名文件
                - overwrite: 覆盖文件
            file: 上传的文件内容


        Returns:
            简单上传结果
        """

        params = {
            "method": "upload",
            "path": path,
            "ondup": ondup,
        }

        respjson = self.auth._do_request("POST", url, params=params, files=file).json()

        return respjson

    @validate_call
    def locateupload(
        self,
        path: str,
        uploadid: str,
    ) -> dict[str, Any] | None:
        """获取上传域名

        本接口用于获取上传域名.

        上传文件数据时, 需要先通过此接口获取上传域名. 可使用返回结果servers字段中的 https 协议的任意一个域名.

        对应百度的API接口: [https://pan.baidu.com/union/doc/Mlvw5hfnr](https://pan.baidu.com/union/doc/Mlvw5hfnr)

        Args:
            path (str): 上传后使用的文件绝对路径
            uploadid (str): 上传ID

        Returns:
            包含上传域名的字典

        """
        params = {
            "method": "locateupload",
            "appid": 250528,
            "path": path,
            "uploadid": uploadid,
            "upload_version": "2.0",
        }
        respjson = self.auth._do_request("GET", API.UploadPath.LOCATEUPLOAD, params=params).json()
        return respjson


class UploadFile:
    """上传文件类, 负责将本地文件分片上传到百度网盘.  (使用多线程上传)

    Attributes:
        up (Upload): 上传对象的实例.

    Example:
    ```python
    from cpanbd import UploadFile, APPNAME

    pan = UploadFile()
    local_filename = "tdata/xxx/Robot0309.zip"
    upload_path = f"/apps/{APPNAME}/tdata/xxx/Robot0309.zip"
    # 上传文件到网盘
    pan.upload_file(
        local_filename=local_filename,
        upload_path=upload_path,
        isdir=0,
        rtype=1,
        bs=32,
        show_progress=True,
    )
    # 如果要批量,只需要循环即可
    ```
    """

    def __init__(self, auth: Auth, userinfo: Optional[UserInfoModel] = None):
        """上传文件类
        
        Args:
            auth: Auth 类实例
            userinfo: 用户信息模型实例
        
        """
        self.up = Upload(auth)
        self.userinfo = userinfo

    def upload_part(
        self,
        server_url: str,
        upload_path: str,
        uploadid: str,
        idx: int,
        chunk: bytes,
        expected_md5: str,
        progress: dict,
        show_progress: bool = True,
    ) -> int:
        """
        上传单个文件分片并更新上传进度.

        Args:
            server_url (str): 上传服务器的 URL.
            upload_path (str): 文件在网盘中的目标路径.
            uploadid (str): 上传会话的 ID.
            idx (int): 当前分片的索引.
            chunk (bytes): 当前分片的二进制数据.
            expected_md5 (str): 当前分片的预期 MD5 值.
            progress (Dict[str, object]): 包含上传进度信息的字典.

        Returns:
            int: 成功上传的分片索引.

        Raises:
            Exception: 如果上传失败或 MD5 校验不一致.
        """
        files = {"file": ("part", chunk)}
        res = self.up.upload_part(
            url=server_url + "/rest/2.0/pcs/superfile2",
            path=upload_path,
            uploadid=uploadid,
            partseq=idx,
            files=files,
        )
        if not res or not res.get("md5"):
            raise Exception(f"上传分片失败: {res}")
        if res["md5"] != expected_md5:
            raise Exception(f"分片 {idx} 的 MD5 不一致: 预期 {expected_md5}, 实际 {res['md5']}")

        if progress["lock"]:
            progress["uploaded"] += 1
            if show_progress:
                percent = (progress["uploaded"] / progress["total"]) * 100
                print(f"\r上传进度: {percent:.2f}%", end="", flush=True)
        return idx

    @validate_call
    def _upload_file_multi(
        self,
        local_filename: str,
        upload_path: str,
        isdir: Literal[0, 1] = 0,
        rtype: Literal[1, 2, 3] = 1,
        max_workers: Optional[int] = None,
        bs: Literal[4, 16, 32] = 4,
        show_progress: bool = True,
    ) -> None | dict:
        """
        使用多线程方式将本地文件上传到百度网盘.
        """
        if self.userinfo is None:
            block_size=4
        elif self.userinfo.viptype == 1:
            block_size=16
        elif self.userinfo.viptype == 2:
            block_size=32
        else:
            block_size=4
        block_size = block_size * 1024 * 1024  # Convert MB to bytes

        file_path = Path(local_filename)
        file_size = file_path.stat().st_size

        content_md5 = calculate_md5(file_path)  # 文件MD5，32位小写
        slice_md5 = calculate_slice_md5(file_path)  # 文件前256KB的MD5
        block_list = get_file_md5_blocks(file_path, block_size=block_size)

        # 预创建文件
        res1 = self.up.precreate(
            path=upload_path,
            size=file_size,
            isdir=isdir,
            block_list=block_list,
            rtype=rtype,
            content_md5=content_md5,
            slice_md5=slice_md5,
        )
        if not res1 or res1.get("errno") != 0:
            print(f"预创建失败: {res1}")
            return
        uploadid = res1["uploadid"]
        # 获取上传地址
        res2 = self.up.locateupload(
            path=upload_path,
            uploadid=uploadid,
        )

        if not res2 or not res2.get("servers"):
            print(f"获取上传地址失败: {res2}")
            return
        server_url = res2["servers"][0]["server"]

        # 多线程上传分片
        # 计算可用的线程数
        m = os.cpu_count() or 1
        max_workers = m - 1 if max_workers is None else max_workers
        max_workers = min(max_workers, len(block_list))
        # print(f"开始多线程上传分片, 线程数: {max_workers}")
        progress: dict = {"uploaded": 0, "total": len(block_list), "lock": Lock()}
        with file_path.open("rb") as f:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = []
                for idx, expected_md5 in enumerate(block_list):
                    f.seek(idx * block_size)
                    chunk = f.read(block_size)
                    if not chunk:
                        break  # 文件读取完毕
                    future = executor.submit(
                        self.upload_part,
                        server_url,
                        upload_path,
                        uploadid,
                        idx,
                        chunk,
                        expected_md5,
                        progress,
                        show_progress,
                    )
                    futures.append(future)

                for future in as_completed(futures):
                    try:
                        idx = future.result()
                    except Exception as e:
                        print(f"\n分片上传失败: {e}")
                        return

        # 创建文件
        res3 = self.up.create(
            path=str(upload_path),
            size=str(file_size),
            isdir="0" if isdir == 0 else "1",
            block_list=json.dumps(block_list, separators=(",", ":")),
            uploadid=str(uploadid),
            rtype=rtype,
        )
        print("\n✅ 所有分片上传完成")
        return res3

    @validate_call
    def _upload_file_loop(
        self,
        local_filename: str,
        upload_path: str,
        isdir: Literal[0, 1] = 0,
        rtype: Literal[1, 2, 3] = 1,
        max_workers: Optional[int] = None,
        bs: Literal[4, 16, 32] = 32,
        show_progress: bool = True,
    ) -> None | dict:
        """
        使用多线程方式将本地文件上传到百度网盘.
        """
        block_size = 4 * 1024 * 1024  # 4MB

        file_path = Path(local_filename)
        file_size = file_path.stat().st_size

        content_md5 = calculate_md5(file_path)  # 文件MD5，32位小写
        slice_md5 = calculate_slice_md5(file_path)  # 文件前256KB的MD5
        block_list = get_file_md5_blocks(file_path, block_size=block_size)

        # 预创建文件
        res1 = self.up.precreate(
            path=upload_path,
            size=file_size,
            isdir=isdir,
            block_list=block_list,
            rtype=rtype,
            content_md5=content_md5,
            slice_md5=slice_md5,
        )
        if not res1 or res1.get("errno") != 0:
            print(f"预创建失败: {res1}")
            return
        uploadid = res1["uploadid"]
        # 获取上传地址
        res2 = self.up.locateupload(
            path=upload_path,
            uploadid=uploadid,
        )

        if not res2 or not res2.get("servers"):
            print(f"获取上传地址失败: {res2}")
            return
        server_url = res2["servers"][0]["server"]
        # 循环上传分片
        progress: dict = {"uploaded": 0, "total": len(block_list), "lock": Lock()}
        with file_path.open("rb") as f:
            for idx, expected_md5 in enumerate(block_list):
                f.seek(idx * block_size)
                chunk = f.read(block_size)
                if not chunk:
                    break  # 文件读取完毕
                try:
                    self.upload_part(
                        server_url,
                        upload_path,
                        uploadid,
                        idx,
                        chunk,
                        expected_md5,
                        progress,
                        show_progress,
                    )
                except Exception as e:
                    print(f"\n{local_filename}分片上传失败: {e}")
                    return
        # 创建文件
        res3 = self.up.create(
            path=str(upload_path),
            size=str(file_size),
            isdir="0" if isdir == 0 else "1",
            block_list=json.dumps(block_list, separators=(",", ":")),
            uploadid=str(uploadid),
            rtype=rtype,
        )
        print(f"\n✅ {local_filename} 上传完成")
        return res3

    @validate_call
    def upload_folder(
        self,
        local_folder: str,
        upload_path: str,
        rtype: Literal[1, 2, 3] = 1,
        file_max_workers: Optional[int] = None,
        chunk_max_workers: Optional[int] = None,
        bs: Literal[4, 16, 32] = 4,
        show_progress: bool = False,
        exclude_patterns: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """
        递归上传本地文件夹到百度网盘(使用多线程并发上传多个文件).

        Args:
            local_folder (str): 本地文件夹的路径.
            upload_path (str): 文件夹在网盘中的目标路径.
            rtype (Literal[1, 2, 3]): 文件命名策略, 默认为 1.
                1: 当path冲突时, 进行重命名
                2: 当path冲突且block_list不同时, 进行重命名
                3: 当云端存在同名文件时, 对该文件进行覆盖
            file_max_workers (int): 文件级并发线程数, 默认为 CPU核心数-1.
            chunk_max_workers (int): 单个文件分片上传的最大并发线程数, 默认为 CPU核心数-1.
            bs (Literal[4, 16, 32]): 分片大小, 单位为 MB, 默认为 4MB.
            show_progress (bool): 是否显示上传进度, 默认为 False.
            exclude_patterns (list[str]): 要排除的文件/文件夹模式列表，支持通配符，如 ['*.tmp', '__pycache__', '.git']

        Returns:
            dict: 包含上传结果的字典，包括成功和失败的文件列表

        Note:
            - 使用两层多线程: 文件级并发 + 每个文件内部的分片并发
            - file_max_workers: 控制同时上传多少个文件
            - chunk_max_workers: 控制每个文件内部同时上传多少个分片

        Example:
            ```python
            from cpanbaidu import PanBaiduOpenAPI

            cpan = PanBaiduOpenAPI()
            result = cpan.upload.upload_folder(
                local_folder="./my_project",
                upload_path="/apps/cpanbaidu/my_project",
                file_max_workers=3,  # 同时上传3个文件
                chunk_max_workers=4,  # 每个文件使用4个线程上传分片
                exclude_patterns=['*.pyc', '__pycache__', '.git', 'node_modules']
            )
            print(f"成功上传: {result['success_count']} 个文件")
            print(f"失败: {result['failed_count']} 个文件")
            ```
        """
        from fnmatch import fnmatch

        folder_path = Path(local_folder)
        if not folder_path.exists():
            raise FileNotFoundError(f"文件夹不存在: {local_folder}")
        if not folder_path.is_dir():
            raise ValueError(f"路径不是文件夹: {local_folder}")

        # 默认排除模式
        if exclude_patterns is None:
            exclude_patterns = []

        # 收集所有需要上传的文件
        files_to_upload = []

        def should_exclude(path: Path) -> bool:
            """检查路径是否应该被排除"""
            for pattern in exclude_patterns:
                # 检查文件名或相对路径是否匹配模式
                if fnmatch(path.name, pattern):
                    return True
                # 检查完整相对路径
                try:
                    rel_path = path.relative_to(folder_path)
                    for part in rel_path.parts:
                        if fnmatch(part, pattern):
                            return True
                except ValueError:
                    pass
            return False

        for item in folder_path.rglob("*"):
            if item.is_file() and not should_exclude(item):
                # 计算相对路径
                rel_path = item.relative_to(folder_path)
                # 构建网盘路径
                remote_path = f"{upload_path.rstrip('/')}/{rel_path.as_posix()}"
                files_to_upload.append((str(item), remote_path))

        total_files = len(files_to_upload)
        if total_files == 0:
            return {
                "success": [],
                "failed": [],
                "success_count": 0,
                "failed_count": 0,
                "total": 0,
            }

        # 上传结果统计
        results = {
            "success": [],
            "failed": [],
            "success_count": 0,
            "failed_count": 0,
            "total": total_files,
        }

        # 计算文件级并发数
        m = os.cpu_count() or 1
        file_max_workers = m - 1 if file_max_workers is None else file_max_workers
        file_max_workers = min(file_max_workers, total_files)

        # 使用线程锁保护结果统计
        results_lock = Lock()

        def upload_single_file(idx: int, local_file: str, remote_file: str):
            """上传单个文件的辅助函数"""
            file_name = Path(local_file).name
            try:
                # 开始上传（不显示进度条，避免多线程混乱）
                result = self._upload_file_loop(
                    local_filename=local_file,
                    upload_path=remote_file,
                    isdir=0,
                    rtype=rtype,
                    max_workers=chunk_max_workers,  # 每个文件内部的分片上传线程数
                    bs=bs,
                    show_progress=False,  # 关闭单个文件的进度显示
                )

                with results_lock:
                    if result:
                        results["success"].append(
                            {
                                "local_path": local_file,
                                "remote_path": remote_file,
                                "result": result,
                            }
                        )
                        results["success_count"] += 1
                        if show_progress:
                            # 只在完成时输出一行
                            print(f"✅ [{results['success_count'] + results['failed_count']}/{total_files}] {file_name}")
                    else:
                        results["failed"].append(
                            {
                                "local_path": local_file,
                                "remote_path": remote_file,
                                "error": "上传返回None",
                            }
                        )
                        results["failed_count"] += 1
                        if show_progress:
                            print(f"❌ [{results['success_count'] + results['failed_count']}/{total_files}] {file_name} (返回None)")

            except Exception as e:
                with results_lock:
                    results["failed"].append(
                        {
                            "local_path": local_file,
                            "remote_path": remote_file,
                            "error": str(e),
                        }
                    )
                    results["failed_count"] += 1
                    if show_progress:
                        error_msg = str(e)[:50]  # 限制错误信息长度
                        print(f"❌ [{results['success_count'] + results['failed_count']}/{total_files}] {file_name} ({error_msg})")

        # 使用多线程并发上传文件
        print(f"🚀 开始多线程上传, 文件并发数: {file_max_workers}")
        with ThreadPoolExecutor(max_workers=file_max_workers) as executor:
            futures = []
            for idx, (local_file, remote_file) in enumerate(files_to_upload, 1):
                future = executor.submit(upload_single_file, idx, local_file, remote_file)
                futures.append(future)

            # 等待所有任务完成
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    if show_progress:
                        print(f"❌ 文件上传任务异常: {e}")

        # 打印总结
        print(f"\n{'=' * 60}")
        print("📈 上传完成统计:")
        print(f"   ✅ 成功: {results['success_count']} 个文件")
        print(f"   ❌ 失败: {results['failed_count']} 个文件")
        print(f"   📊 总计: {results['total']} 个文件")
        print(f"{'=' * 60}")

        # 如果有失败的文件，显示详情
        if results["failed_count"] > 0:
            print("\n❌ 失败的文件:")
            for item in results["failed"]:
                print(f"   - {item['local_path']}: {item['error']}")
        results["errno"] = 0
        return results

    # 上传单个文件采用多线程
    @validate_call
    def upload_file(
        self,
        local_filename: str,
        upload_path: str,
        isdir: Literal[0, 1] = 0,
        rtype: Literal[1, 2, 3] = 1,
        max_workers: Optional[int] = None,
        bs: Literal[4, 16, 32] = 4,
        show_progress: bool = True,
    ) -> None | dict:
        """
        上传单个文件到百度网盘，采用多线程分片上传方式.

        Args:
            local_filename (str): 本地文件的路径.
            upload_path (str): 文件在网盘中的目标路径.
            isdir (Literal[0, 1]): 是否为目录，默认为 0（文件）.
            rtype (Literal[1, 2, 3]): 文件命名策略，默认为 1.
                1: 当path冲突时, 进行重命名
                2: 当path冲突且block_list不同时, 进行重命名
                3: 当云端存在同名文件时, 对该文件进行覆盖
            max_workers (int): 分片上传的最大并发线程数，默认为 CPU核心数-1.
            bs (Literal[4, 16, 32]): 分片大小，单位为 MB，默认为 4MB.
            show_progress (bool): 是否显示上传进度，默认为 True.

        Returns:
            dict: 包含上传结果的字典
        """
        return self._upload_file_multi(
            local_filename=local_filename,
            upload_path=upload_path,
            isdir=isdir,
            rtype=rtype,
            max_workers=max_workers,
            bs=bs,
            show_progress=show_progress,
        )
