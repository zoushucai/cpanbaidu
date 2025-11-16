import json
from typing import Any, Literal, Optional

from pydantic import validate_call

from .Auth import Auth
from .utils.Constants import API
from .model.FileModel import listallParams, listParams
from .model.Base import UserInfoModel

class File:
    def __init__(self, auth: Auth, userinfo: Optional[UserInfoModel] = None):
        """文件操作类
        
        Args:
            auth: Auth 类实例
            userinfo: 用户信息模型实例
        
        """
        self.auth = auth
        self.userinfo = userinfo

    @validate_call
    def list_files(
        self,
        dir: str = "/",
        order: Literal["name", "size", "time"] = "name",
        desc: Literal[0, 1] = 1,
        start: int = 0,
        limit: int = 100,
        web: Literal[0, 1] = 1,
        folder: Literal[0, 1] = 0,
        showempty: Literal[0, 1] = 0,
    ) -> dict[str, Any] | None:
        """获取文件列表


        本接口用于获取用户网盘中指定目录下的文件列表. 返回的文件列表支持排序、分页等操作. (不递归,只能是当前目录下的文件列表)

        对应百度的API接口: [https://pan.baidu.com/union/doc/nksg0sat9](https://pan.baidu.com/union/doc/nksg0sat9)


        Args:
            dir: 目录名称绝对路径, 必须/开头；
            order: 排序方式, 默认为name, 可选值为name, size, time
            desc: 是否降序, 0为升序, 1为降序, 默认为1
            start: 起始位置, 默认为0
            limit: 返回数量, 查询数目, 默认为1000
            web: 是否web模式, 默认为1,  为1时返回缩略图地址
            folder: 是否只显示文件夹, 默认为0,  为1时只显示文件夹
            showempty: 是否显示空文件夹, 默认为0,  为1时显示空文件夹

        Returns:
            dict: 返回的文件列表, 包含文件名、文件大小、文件类型等信息
        """
        params = listParams(
            dir=dir,
            order=order,
            desc=desc,
            start=start,
            limit=limit,
            web=web,
            folder=folder,
            showempty=showempty,
        ).model_dump()
        respjson = self.auth.request_json("GET", API.FilePath.LIST, params=params)
        return respjson

    @validate_call
    def listall(
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
    ) -> dict[str, Any] | None:
        """递归获取文件列表

        本接口可以递归获取指定目录下的文件列表. 当目录下存在文件夹, 并想获取到文件夹下的子文件时, 可以设置 recursion 参数为1, 即可获取到更深目录层级的文件.

        对应百度的API接口: [https://pan.baidu.com/union/doc/Zksg0sb73](https://pan.baidu.com/union/doc/Zksg0sb73)

        Args:
            path: 目录名称绝对路径, 必须/开头；
            recursion: 是否递归,0为否, 1为是, 默认为0
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
        params = listallParams(
            path=path,
            recursion=recursion,
            order=order,
            desc=desc,
            start=start,
            limit=limit,
            ctime=ctime,
            mtime=mtime,
            web=web,
            device_id=device_id,
        ).model_dump(exclude_none=True)
        respjson = self.auth.request_json("GET", API.FilePath.LISTALL, params=params)
        return respjson

    @validate_call
    def doclist(
        self,
        parent_path: str = "/",
        page: int = 1,
        num: int = 100,
        order: Literal["name", "size", "time"] = "name",
        desc: int = 1,
        recursion: int = 0,
        web: int = 0,
    ) -> dict[str, Any] | None:
        """获取文档列表

        本接口用于获取用户指定目录下的文档列表.

        对应百度的API接口: [https://pan.baidu.com/union/doc/Eksg0saqp](https://pan.baidu.com/union/doc/Eksg0saqp)

        Args:
            parent_path: 目录名称绝对路径, 必须/开头；
            page: 页码, 从1开始,  如果不指定页码, 则为不分页模式, 返回所有的结果. 如果指定page参数, 则按修改时间倒序排列
            num: 一页返回的文档数,  默认值为1000, 建议最大值不超过1000
            order: 排序字段: time(修改时间), name(文件名), size(文件大小)
            desc: 0为升序, 1为降序, 默认为1
            recursion: 是否需要递归, 0为不需要, 1为需要, 默认为0, 递归是指:当目录下有文件夹, 使用此参数, 可以获取到文件夹下面的文档
            web: 是否web模式, 默认为0,  为1时返回缩略图地址

        """
        # 检查path,必须以/开头
        if not parent_path.startswith("/"):
            raise ValueError("parent_path must start with /")

        params = {
            "parent_path": parent_path,
            "page": page,
            "num": num,
            "order": order,
            "desc": desc,
            "recursion": recursion,
            "web": web,
            "method": "doclist",
        }
        respjson = self.auth.request_json("GET", API.FilePath.DOCLIST, params=params)
        return respjson

    @validate_call
    def imagelist(
        self,
        parent_path: str = "/",
        page: int = 1,
        num: int = 100,
        order: Literal["name", "size", "time"] = "name",
        desc: int = 1,
        recursion: int = 0,
        web: int = 0,
    ) -> dict[str, Any] | None:
        """获取图片列表

        本接口用于获取用户指定目录下的图片列表.

        对应百度的API接口: [https://pan.baidu.com/union/doc/bksg0sayv](https://pan.baidu.com/union/doc/bksg0sayv)

        Args:
            parent_path: 目录名称绝对路径, 必须/开头；
            page: 页码, 从1开始,  如果不指定页码, 则为不分页模式, 返回所有的结果. 如果指定page参数, 则按修改时间倒序排列
            num: 一页返回的文档数,  默认值为1000, 建议最大值不超过1000
            order: 排序字段: time(修改时间), name(文件名), size(文件大小)
            desc: 0为升序, 1为降序, 默认为1
            recursion: 是否需要递归, 0为不需要, 1为需要, 默认为0, 递归是指:当目录下有文件夹, 使用此参数, 可以获取到文件夹下面的文档
            web: 是否web模式, 默认为0,  为1时返回缩略图地址

        其他参数请参考API文档

        """
        # 检查path,必须以/开头
        if not parent_path.startswith("/"):
            raise ValueError("parent_path must start with /")

        params = {
            "method": "imagelist",
            "parent_path": parent_path,
            "page": page,
            "num": num,
            "order": order,
            "desc": desc,
            "recursion": recursion,
            "web": web,
        }
        respjson = self.auth.request_json("GET", API.FilePath.IMAGELIST, params=params)
        return respjson

    @validate_call
    def videolist(
        self,
        parent_path: str = "/",
        page: int = 1,
        num: int = 100,
        order: Literal["name", "size", "time"] = "name",
        desc: int = 1,
        recursion: int = 0,
        web: int = 1,
    ) -> dict[str, Any] | None:
        """获取视频列表

        本接口用于获取用户指定目录下的视频列表.

        对应百度的API接口: [https://pan.baidu.com/union/doc/Sksg0saw0](https://pan.baidu.com/union/doc/Sksg0saw0)

        Args:
            parent_path: 目录名称绝对路径, 必须/开头；
            page: 页码, 从1开始,  如果不指定页码, 则为不分页模式, 返回所有的结果. 如果指定page参数, 则按修改时间倒序排列
            num: 一页返回的文档数,  默认值为1000, 建议最大值不超过1000
            order: 排序字段: time(修改时间), name(文件名), size(文件大小)
            desc: 0为升序, 1为降序, 默认为1
            recursion: 是否需要递归, 0为不需要, 1为需要, 默认为0, 递归是指:当目录下有文件夹, 使用此参数, 可以获取到文件夹下面的文档
            web: 是否web模式, 默认为1,  为1时返回缩略图地址

        其他参数请参考API文档

        """
        # 检查path,必须以/开头
        if not parent_path.startswith("/"):
            raise ValueError("parent_path must start with /")

        params = {
            "method": "videolist",
            "parent_path": parent_path,
            "page": page,
            "num": num,
            "order": order,
            "desc": desc,
            "recursion": recursion,
            "web": web,
        }
        respjson = self.auth.request_json("GET", API.FilePath.VIDEOLIST, params=params)
        return respjson

    @validate_call
    def btlist(
        self, parent_path: str = "/", page: int = 1, num: int = 100, order: Literal["name", "size", "time"] = "name", desc: int = 1, recursion: int = 0
    ) -> dict[str, Any] | None:
        """获取bt列表

        本接口用于获取用户指定目录下的bt列表.

        对应百度的API接口: [https://pan.baidu.com/union/doc/xksg0sb1d](https://pan.baidu.com/union/doc/xksg0sb1d)

        Args:
            parent_path: 目录名称绝对路径, 必须/开头；
            page: 页码, 从1开始,  如果不指定页码, 则为不分页模式, 返回所有的结果. 如果指定page参数, 则按修改时间倒序排列
            num: 一页返回的文档数,  默认值为1000, 建议最大值不超过1000
            order: 排序字段: time(修改时间), name(文件名), size(文件大小)
            desc: 0为升序, 1为降序, 默认为1
            recursion: 是否需要递归, 0为不需要, 1为需要, 默认为0, 递归是指:当目录下有文件夹, 使用此参数, 可以获取到文件夹下面的文档

        其他参数请参考API文档
        """
        # 检查path,必须以/开头
        if not parent_path.startswith("/"):
            raise ValueError("parent_path must start with /")

        params = {
            "method": "btlist",
            "parent_path": parent_path,
            "page": page,
            "num": num,
            "order": order,
            "desc": desc,
            "recursion": recursion,
        }
        respjson = self.auth.request_json("GET", API.FilePath.BTLIST, params=params)
        return respjson

    @validate_call
    def categoryinfo(
        self,
        category: int = 4,
        parent_path: str = "/",
        recursion: int = 0,
    ) -> dict[str, Any] | None:
        """获取分类文件总个数

        本接口用于获取用户指定目录下指定类型的文件数量.

        对应百度的API接口: [https://pan.baidu.com/union/doc/dksg0sanx](https://pan.baidu.com/union/doc/dksg0sanx)

        Args:
            category: 文件类型, 1 视频、2 音频、3 图片、4 文档、5 应用、6 其他、7 种子
            parent_path: 目录名称绝对路径, 必须/开头；
            recursion: 是否递归, 0 不递归、1 递归, 默认0

        """
        # 检查path,必须以/开头
        if not parent_path.startswith("/"):
            raise ValueError("parent_path must start with /")

        params = {
            "category": category,
            "parent_path": parent_path,
            "recursion": recursion,
        }
        respjson = self.auth.request_json("GET", API.FilePath.CATEGORYINFO, params=params)
        return respjson

    @validate_call
    def categorylist(
        self,
        category: str = "1",
        show_dir: Literal[0, 1] = 0,
        parent_path: str = "/",
        recursion: int = 0,
        ext: Optional[str] = None,
        start: int = 0,
        limit: int = 100,
        order: Literal["name", "size", "time"] = "name",
        desc: str = "0",
        device_id: Optional[str] = None,
    ) -> dict[str, Any] | None:
        """获取分类文件列表

        本接口用于获取用户目录下指定类型的文件列表.

        对应百度的API接口: [https://pan.baidu.com/union/doc/Sksg0sb40](https://pan.baidu.com/union/doc/Sksg0sb40)

        Args:
            category: 文件类型, 1 视频、2 音频、3 图片、4 文档、5 应用、6 其他、7 种子, 多个category使用英文逗号分隔, 示例:3,4
            show_dir: 是否展示文件夹，0:否(默认) 1:是
            parent_path: 目录名称绝对路径, 必须/开头；
            recursion: 是否需要递归，0 不递归、1 递归，默认0 （注意recursion=1时不支持show_dir=1）
            ext: 需要的文件格式, 多个格式以英文逗号分隔, 示例: txt,epub, 默认为category下所有格式
            start: 查询起点, 默认为0, 当返回has_more=1时, 应使用返回的cursor作为下一次查询的起点
            limit: 查询条数, 默认为1000, 最大值为1000
            order: 排序字段: time(修改时间), name(文件名), size(文件大小)
            desc: 0为升序, 1为降序, 默认为0
            device_id: 设备ID, 硬件设备必传

        其他参数请参考API文档

        """
        # 检查path,必须以/开头
        if not parent_path.startswith("/"):
            raise ValueError("parent_path must start with /")
        # 检查参数冲突：recursion 和 show_dir 不能同时为 1
        if recursion == 1 and show_dir == 1:
            raise ValueError("百度 API 限制: recursion 和 show_dir 不能同时为 1")

        params = {
            "method": "categorylist",
            "category": category,
            "show_dir": show_dir,
            "parent_path": parent_path,
            "recursion": recursion,
            "ext": ext,
            "start": start,
            "limit": limit,
            "order": order,
            "desc": desc,
            "device_id": device_id,
        }
        respjson = self.auth.request_json("GET", API.FilePath.CATEGORYLIST, params=params)
        return respjson

    # 查询文件信息
    @validate_call
    def search_fileinfo(
        self,
        fsid: list[int],
        dlink: Literal[0, 1] = 0,
        path: Optional[str] = None,
        thumb: Literal[0, 1] = 0,
        extra: Literal[0, 1] = 0,
        needmedia: Literal[0, 1] = 0,
        detail: Literal[0, 1] = 0,
        device_id: Optional[str] = None,
        from_apaas: Optional[Literal[0, 1]] = None,
    ) -> dict[str, Any] | None:
        """查询文件信息
        本接口可用于获取用户指定文件的meta信息。支持查询多个或一个文件的meta信息，meta信息包括文件名字、文件创建时间、文件的下载地址等。


        对应百度的API接口: [https://pan.baidu.com/union/doc/Fksg0sbcm](https://pan.baidu.com/union/doc/Fksg0sbcm)

        Args:
            fsid: 文件id数组，数组中元素是uint64类型，数组大小上限是：100
            dlink: 是否需要下载地址，0为否，1为是，默认为0。获取到dlink后，参考下载文档进行下载操作
            path: 查询共享目录或专属空间内文件时需要。含义并非待查询文件的路径，而是查询特定目录下文件的开关参数。
            thumb: 是否需要缩略图地址，0为否，1为是，默认为0
            extra: 图片是否需要拍摄时间、原图分辨率等其他信息，0 否、1 是，默认0
            needmedia: 视频是否需要展示时长信息，needmedia=1时，返回 duration 信息时间单位为秒 （s），转换为向上取整。 0 否、1 是，默认0
            detail: 视频是否需要展示长，宽等信息。 0 否、1 是，默认0。返回信息在media_info字段内，参考响应示例的视频文件。
            device_id: 设备ID，硬件设备必传
            from_apaas: 为下载地址(dlink)附加极速流量权益。用户通过此dlink产生下载行为时，消耗等同于文件大小的极速流量权益。此权益为付费权益，如需要购买极速流量权益服务，可联系商务合作邮箱：ext_mars-union@baidu.com 进行咨询，否则此参数无效。

        其他参数请参考API文档
        """
        params = {
            "method": "filemetas",
            "fsids": str(json.dumps(fsid, separators=(",", ":"))),
            "dlink": dlink,
            "path": path,
            "thumb": thumb,
            "extra": extra,
            "needmedia": needmedia,
            "detail": detail,
            "device_id": device_id,
            "from_apaas": from_apaas,
        }
        respjson = self.auth.request_json("GET", API.FilePath.FILEMETAS, params=params)
        return respjson

    @validate_call
    def search_by_keyword(
        self,
        key: str = "",
        dir: str = "/",
        category: int = 4,
        num: int = 500,  # 不能修改
        recursion: int = 0,
        web: int = 0,
        device_id: Optional[str] = None,
    ) -> dict[str, Any] | None:
        """搜索文件（关键词搜索）

        本接口用于获取用户指定目录下, 包含指定关键字的文件列表.

        对应百度的API接口: [https://pan.baidu.com/union/doc/zksg0sb9z](https://pan.baidu.com/union/doc/zksg0sb9z)

        Args:
            key: 搜索关键字，最大30字符（UTF8格式）
            dir: 搜索目录，默认根目录
            category: 文件类型，1 视频、2 音频、3 图片、4 文档、5 应用、6 其他、7 种子
            num: 默认为500，不能修改
            recursion: 是否递归，带这个参数就会递归，否则不递归，0 不递归、1 递归，默认0
            web: 是否展示缩略图信息，带这个参数会返回缩略图信息，否则不展示缩略图信息
            device_id: 设备ID，设备注册接口下发，硬件设备必传

        其他参数请参考API文档

        """

        # 检查path,必须以/开头
        if not dir.startswith("/"):
            raise ValueError("dir must start with /")

        params = {
            "method": "search",
            "key": key,
            "dir": dir,
            "category": category,
            "num": 500,
            "recursion": recursion,
            "web": web,
            "device_id": device_id,
        }
        respjson = self.auth.request_json("GET", API.FilePath.SEARCH, params=params)
        return respjson

    @validate_call
    def unisearch(
        self,
        query: str,
        dir: str = "/",
        category: list[int] | None = None,
        num: int = 500,
        stream: int = 0,
        search_type: int = 0,
        sources: Optional[str] = None,
    ):
        """搜索文件（语义搜索）

        本接口用于获取用户指定目录下, 包含指定关键字的文件列表.

        对应百度的API接口: [https://pan.baidu.com/union/doc/unisearch](https://pan.baidu.com/union/doc/unisearch)

        Args:
            query: 搜索query
            dir: 指定路径搜索, 默认根目录
            category: 文件类型。1-视频、2-音频、3-图片、4-文档、5-应用、6-其他、7-种子，多个category使用英文逗号分隔, 示例: [3,4]
            num: 搜索返回的最大数量, 500
            stream: 是否流式响应，0 关闭，1 开启，默认0
            search_type: 	搜索方式。

                - 0-简单搜索（query为关键词
                - 1-语义搜索（query为复杂的自然语言描述）
                - 2-自动（按query长度自动区分简单/语义搜索，目前『自动』策略为：5字以上走语义搜索，5字及以下走简单搜索）

            sources: 搜索来源。

                - 通过query的关键词搜索：4-文件名关键词搜索，5-图片OCR搜索（图片内文字），11-文档内容搜索（文档文本关键词），14-图片语义搜索（图片时间/地点/分类等），13-卡证搜索
                - 通过query的语义向量搜索：7-文档向量搜索，8-视频向量搜索，9-音频向量搜索
                - sources为空时，search_type为0（简单搜索）时sources默认设置为[4,5,11,13,14]，search_type为1（语义搜索）时sources默认设置为[4,5,11,13,14,7,8,9]
        """

        params = {
            "scene": "mcpserver",  # 固定
            "query": query,
            "dir": dir,
            "category": json.dumps(category) if category else None,
            "num": min(num, 500),
            "stream": stream,
            "search_type": search_type,
            "sources": sources,
        }
        respjson = self.auth.request_json("POST", API.FilePath.UNISEARCH, params=params, json={})
        return respjson

    @validate_call
    def filemanager(
        self,
        opera: Literal["copy", "move", "rename", "delete"],
        filelist: list[dict[str, Any]],
        aasync: Literal[0, 1, 2] = 1,
        ondup: Literal["fail", "newcopy", "overwrite", "skip"] = "fail",
    ) -> dict[str, Any] | None:
        """管理文件

        本接口用于对文件进行操作, 包括复制、移动、重命名、删除等操作.

        对应百度的API接口: [https://pan.baidu.com/union/doc/mksg0s9l4](https://pan.baidu.com/union/doc/mksg0s9l4)

        Args:
            opera: 文件操作参数, 可实现文件复制、移动、重命名、删除, 依次对应的参数值为: copy, move, rename, delete
            aasync: 0 同步, 1 自适应, 2 异步
            filelist: 文件操作列表, 数组中元素是object类型, 数组大小上限是:100
            ondup: 全局ondup,遇到重复文件的处理策略, fail(默认, 直接返回失败)、newcopy(重命名文件)、overwrite、skip

        filelist 参数示例:

            ```
            [{"path":"/test/123456.docx","dest":"/test/abc","newname":"11223.docx"}]【copy/move示例】

            [{"path":"/test/123456.docx","newname":"123.docx"}]【rename示例】

            ["/test/123456.docx"]【delete示例】
            ```
        Returns:
            文件操作结果
        """
        params = {
            "method": "filemanager",
            "opera": opera,
            "aasync": aasync,
            "filelist": str(json.dumps(filelist, separators=(",", ":"))),
            "ondup": ondup,
        }
        respjson = self.auth.request_json("POST", API.FilePath.FILEMANAGER, params=params, json={})
        return respjson

    def filemetas(self, **kwargs) -> dict[str, Any] | None:
        """查询文件信息，filemetas 方法的别名

        详见 File.search_fileinfo 方法
        """
        return self.search_fileinfo(**kwargs)
