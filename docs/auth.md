
## Auth 类说明

### 1. 使用自己的密钥

在使用百度授权时，必须在当前项目目录下（`.env`）或用户根目录下（`~/.env.baidu`）建立配置文件，并提供以下四个参数：

* `CLIENT_ID`
* `CLIENT_KEY`
* `CLIENT_SECRET`
* `REDIRECT_URI`

> 这四个参数需要在 百度 开发者平台申请，申请通过后才能获得对应的值。



### 2. 使用第三方密钥（作者提供）

如果使用作者提供的第三方密钥，会自动在项目目录（`.env`）或根目录（`~/.env.baidu`）建立配置文件，只需要根据提示进行授权即可



## OAuth类

::: cpanbaidu.authtype.OAuth

## Auth类

::: cpanbaidu.Auth