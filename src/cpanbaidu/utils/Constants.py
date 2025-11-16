## 有关授权的
API_BASE: str = "https://pan.baidu.com"
AUTH_BASE: str = "https://openapi.baidu.com"


class API:
    """百度 接口路径和方法统一管理"""

    AUTH_BASE = AUTH_BASE
    API_BASE = API_BASE

    class Oauth2:
        # 原始的 OAuth2 授权地址
        AUTHORIZE = "https://openapi.baidu.com/oauth/2.0/authorize"
        TOKEN ="https://openapi.baidu.com/oauth/2.0/token"
        REFRESH = "https://openapi.baidu.com/oauth/2.0/token"

    class OAuth2Backend:
        # 后端获取随机码的地址
        STATE_ENDPOINT = "/baiducloud/state"
        # 后端通过code获取token的地址
        TOKEN_ENDPOINT = "/baiducloud/callback"



    # class JWT:
    #     # 百度 没有JWT, 这里只是占位
    #     TOKEN = AUTH_BASE + "/api/v1/access_token"  # 获取访问令牌

    class UserPath:
        USER_INFO = API_BASE + "/rest/2.0/xpan/nas"
        QUOTA = API_BASE + "/api/quota"

    class FilePath:
        # GET /rest/2.0/xpan/file?method=list HTTP/1.1
        LIST = API_BASE + "/rest/2.0/xpan/file"

        # GET /rest/2.0/xpan/multimedia?method=listall HTTP/1.1
        LISTALL = API_BASE + "/rest/2.0/xpan/multimedia"

        # GET /rest/2.0/xpan/file?method=doclist HTTP/1.1
        DOCLIST = API_BASE + "/rest/2.0/xpan/file"

        # GET /rest/2.0/xpan/file?method=imagelist HTTP/1.1
        IMAGELIST = API_BASE + "/rest/2.0/xpan/file"

        # GET /rest/2.0/xpan/file?method=videolist HTTP/1.1
        VIDEOLIST = API_BASE + "/rest/2.0/xpan/file"

        # /GET /rest/2.0/xpan/file?method=btlist HTTP/1.1
        BTLIST = API_BASE + "/rest/2.0/xpan/file"

        # GET /api/categoryinfo HTTP/1.1
        CATEGORYINFO = API_BASE + "/api/categoryinfo"

        # GET /rest/2.0/xpan/multimedia?method=categorylist HTTP/1.1
        CATEGORYLIST = API_BASE + "/rest/2.0/xpan/multimedia"

        # GET /rest/2.0/xpan/multimedia?method=filemetas&access_token=xxx HTTP/1.1
        FILEMETAS = API_BASE + "/rest/2.0/xpan/multimedia"

        # GET /rest/2.0/xpan/file?method=search HTTP/1.1
        SEARCH = API_BASE + "/rest/2.0/xpan/file"

        # POST /xpan/unisearch
        UNISEARCH = API_BASE + "/xpan/unisearch"

        # POST /rest/2.0/xpan/file?method=filemanager HTTP
        FILEMANAGER = API_BASE + "/rest/2.0/xpan/file"

    class UploadPath:
        # 预上传 POST /rest/2.0/xpan/file?method=precreate&access_token=xxx HTTP/1.1
        PRECREATE = API_BASE + "/rest/2.0/xpan/file"

        # 创建文件 POST /rest/2.0/xpan/file?method=create&access_token=xxx HTTP/1.1
        CREATE = API_BASE + "/rest/2.0/xpan/file"

        # 获取上传域名  GET /rest/2.0/pcs/file?method=locateupload HTTPS/1.1
        LOCATEUPLOAD = "https://d.pcs.baidu.com/rest/2.0/pcs/file"



# ERROR_MAP = {
#     40100000: "参数缺失",
#     40101017: "用户验证失败",
#     40110000: "请求异常，需要重试",
#     40140100: "client_id错误",
#     40140101: "code_challenge必填",
#     40140102: "code_challenge_method必须是sha256、sha1、md5之一",
#     40140103: "sign必填",
#     40140104: "sign签名失败",
#     40140105: "生成二维码失败",
#     40140106: "APP ID无效",
#     40140107: "应用不存在",
#     40140108: "应用未审核通过",
#     40140109: "应用已被停用",
#     40140110: "应用已过期",
#     40140111: "APP Secret错误",
#     40140112: "code_verifier长度要求43~128位",
#     40140113: "code_verifier验证失败",
#     40140114: "refresh_token格式错误（防篡改）",
#     40140115: "refresh_token签名校验失败（防篡改）",
#     40140116: "refresh_token无效（已解除授权）",
#     40140117: "access_token刷新太频繁",
#     40140118: "开发者认证已过期",
#     40140119: "refresh_token已过期",
#     40140120: "refresh_token检验失败（防篡改）",
#     40140121: "access_token刷新失败",
#     40140122: "超出授权应用个数上限",
#     40140123: "access_token格式错误（防篡改）",
#     40140124: "access_token签名校验失败（防篡改）",
#     40140125: "access_token无效（已过期或解除授权）",
#     40140126: "access_token校验失败（防篡改）",
#     40140127: "response_type错误",
#     40140128: "redirect_uri缺少协议",
#     40140129: "redirect_uri缺少域名",
#     40140130: "没有配置重定向域名",
#     40140131: "redirect_uri非法域名",
#     40140132: "grant_type错误",
#     40140133: "client_secret验证失败",
#     40140134: "授权码 code验证失败",
#     40140135: "client_id验证失败",
#     40140136: "redirect_uri验证失败（防MITM）",
# }

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
