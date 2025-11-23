from .Auth import Auth

from .User import User
from .Upload import UploadFile
from .Downfile import DownFile
from .utils.Logger import log
from .File import File
from .FileList import FileList
class PanBaiduOpenAPI:
    """
    百度开放接口客户端
    包含用户信息与上传等功能
    """

    def __init__(self, envpath: str | None = None, verbose: bool = False):
        """初始化百度开放接口客户端
        
        Args:
            envpath: 环境变量文件路径,默认None表示自动查找当前目录下的`.env`或用户根目录下的`.env.baidu`
            verbose: 是否启用详细日志输出,默认False
        
        """
        self.log = log
        self.auth = Auth(envpath=envpath, verbose=verbose)
        self.user = User(self.auth)

        self.userinfo = self.user.userinfo
        assert self.userinfo is not None, "用户未授权,请先完成授权流程"
        # 将用户信息传递给其他组件
        self.file = File(self.auth, self.userinfo)
        self.filelist = FileList(self.auth, self.userinfo)
        self.upload = UploadFile(self.auth, self.userinfo)
        self.downfile = DownFile(self.auth, self.userinfo)
        log.info(f"已登录用户: {self.userinfo.username} (ID: {self.userinfo.userid}, ISVIP: {self.userinfo.isvip})")
