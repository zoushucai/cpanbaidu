from pathlib import Path, PurePosixPath

from cpanbaidu.model.Base import UserInfoModel

from .Auth import Auth
from .utils.Constants import UA  
from .File import File
from .utils.download import download_file
from .model.Base import AuthError
from typing import Optional

class DownFile:
    def __init__(self, auth: Auth, userinfo: Optional[UserInfoModel] = None):
        """下载文件类
        
        Args:
            auth: Auth 类实例
            userinfo: 用户信息模型实例
        
        """
        self.auth = auth
        self.file = File(auth, userinfo)
        self.userinfo = userinfo

    def downfile(
        self,
        filebd: str,
        output_path: str,
        overwrite: bool = False,
        verbose: bool = True,
    ) -> None:
        """
        下载百度网盘的单个文件

        !!! note "注意"
            1. 只能下载单个文件,不能下载目录
            2. 百度网盘的文件路径必须以 / 开头, 否则会报错

        !!! error "错误"
            1. 有些时候 md5 验证不通过,但是奇怪的是下载下来的文件可以正确打开,里面的文件也可以正常使用. 难道文件太大? 解密函数有问题?
            2. 待改进

        Args:
            filebd (str): 百度网盘文件路径 (绝对路径), 以 / 开头,只能是一个文件
            output_path (str): 下载文件保存路径
            overwrite (bool): 是否覆盖已存在的文件, 默认 False
            verbose (bool): 是否打印下载进度, 默认 True

        Example:
            ```python
            from cpanbd import DownFile

            pan = DownFile()
            pan.downfile("/我的资源/Y1401-书柜图纸/文件名.txt", "文件名.txt")
            ```
        """
        assert filebd.startswith("/"), "百度网盘文件路径必须以 / 开头"

        parent_dir = str(PurePosixPath(filebd).parent)

        file_list_response = self.file.list_files(dir=parent_dir, web=0)

        if not file_list_response or "list" not in file_list_response:
            print("❌ 无法列出百度网盘文件, 请检查目录或网络. ")
            return
        fileinfo = None
        for item in file_list_response["list"]:
            if item["path"] == filebd and item["isdir"] == 0:
                fileinfo = item
                break
        if not fileinfo:
            print("百度网盘文件不存在")
            return
        fs_id = fileinfo["fs_id"]
        meta_response = self.file.filemetas(fsid=[fs_id], dlink=1)
        if not meta_response or "list" not in meta_response or not meta_response["list"]:
            print("❌ 无法获取文件元信息(dlink 和 md5)")
            return
        meta = meta_response["list"][0]
        dlink = meta["dlink"]
        # 添加 access_token
        access_token = self.auth.get_access_token()
        if "?" in dlink:
            dlink += f"&access_token={access_token}"
        else:
            dlink += f"?access_token={access_token}"
        # md5 = decrypt_md5(meta["md5"])# 已失效

        if verbose:
            print(f"✅ 开始下载: {filebd}")
            print(f"➡️ 保存至: {output_path}")
        if self.userinfo is None:
            block_size=4
        elif self.userinfo.viptype == 1:
            block_size=16
        elif self.userinfo.viptype == 2:
            block_size=32
        else:
            block_size=4
            
        download_file(url=dlink, output_path=output_path, headers={"User-Agent": UA}, overwrite=overwrite, verbose=verbose, block_size = block_size, expected_md5=None)

    # 批量目录
    def downdir(
        self,
        dirbd: str,
        output_path: str,
        overwrite: bool = False,
        verbose: bool = True,
    ) -> None:
        """下载百度网盘目录(含递归)

        Args:
            dirbd (str): 百度网盘目录路径 (绝对路径), 以 / 开头
            output_path (str): 下载文件保存路径
            overwrite (bool): 是否覆盖已存在的文件, 默认 False
            verbose (bool): 是否打印下载进度, 默认 True

        Example:
            ```python
            from cpanbd import DownFile

            pan = DownFile()
            pan.downdir("/我的资源/Y1401-书柜图纸", "tmp")
            ```
        """
        assert dirbd.startswith("/"), "百度网盘目录路径必须以 / 开头"
        has_more = 0  # 是否还有下一页, 0表示无, 1表示有
        cursor = 0  # 当还有下一页时, 为下一次查询的起点
        files = []  # 存储文件信息
        while True:
            listall_response = self.file.listall(path=dirbd, recursion=1, start=cursor, limit=10, web=0)
            if not listall_response or "list" not in listall_response:
                print("❌ 无法列出百度网盘文件, 请检查目录或网络. ")
                return
            files.extend(listall_response["list"])
            has_more = listall_response["has_more"]
            if has_more == 1:
                cursor = listall_response["cursor"]
            else:
                break
        # 过滤掉目录,只保留文件
        files = [file for file in files if file["isdir"] == 0]
        if not files:
            print("❌ 目录下没有文件")
            return
        if verbose:
            print(f"✅ 开始下载: {dirbd}")
            print(f"➡️ 保存至: {output_path}")
        for fileinfo in files:
            filebd = fileinfo["path"]
            fs_id = fileinfo["fs_id"]
            meta_response = self.file.filemetas(fsid=[fs_id], dlink=1)
            if not meta_response or "list" not in meta_response or not meta_response["list"]:
                print(f"❌ 无法获取文件{filebd}的元信息(dlink 和 md5)")
                return

            meta = meta_response["list"][0]
            # dlink = meta["dlink"] + "&access_token=" + os.getenv("BAIDU_ACCESS_TOKEN", "")
            # md5 = decrypt_md5(meta["md5"]) # 已失效

            dlink = meta["dlink"]
            # 添加 access_token
            access_token = self.auth.get_access_token()
            if "?" in dlink:
                dlink += f"&access_token={access_token}"
            else:
                dlink += f"?access_token={access_token}"

            temp = Path(filebd).relative_to(dirbd)
            output_file_path = Path(output_path) / temp
            Path(output_file_path).parent.mkdir(parents=True, exist_ok=True)
            download_file(
                url=dlink,
                output_path=output_file_path,
                headers={"User-Agent": UA},
                overwrite=overwrite,
                verbose=verbose,
                expected_md5=None,
            )
