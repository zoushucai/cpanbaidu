# Welcome to cpanbaidu


百度云盘的python接口文档(非官方), 只实现了部分接口, 仅供学习使用


百度云盘的官方接口文档: [https://pan.baidu.com/union/doc/pksg0s9ns](https://pan.baidu.com/union/doc/pksg0s9ns)

关于授权参考: [Auth](./auth.md)

## 安装

```python
pip install cpanbaidu
```

## 接口

- 参考接口类



## 常用功能

- 下载文件(夹)

```python
from cpanbaidu import PanBaiduOpenAPI

cpan = PanBaiduOpenAPI()
# 下载文件
cpan.downfile.downfile(
    filebd="/apps/cpanbaidu/4.rar",
    output_path="5.rar",
    overwrite=True,
    verbose=True,
)

#下载文件夹
cpan.downfile.downdir(dirbd="/apps/cpanbaidu/downloads", output_path="downloads5", overwrite=True, verbose=True)


``` 


- 上传文件(夹)

```python
from cpanbaidu import PanBaiduOpenAPI

cpan = PanBaiduOpenAPI()
# 上传文件
result = cpan.upload.upload_file(local_filename="4.rar", upload_path="/apps/cpanbaidu/4.rar")
log.info(f"上传结果: {result}")

## 上传文件夹
result = cpan.upload.upload_folder(local_folder="downloads", upload_path="/apps/cpanbaidu/downloads")
log.info(f"上传文件夹结果: {result}")


```


### 封装的接口

- [x] 上传文件(夹)
- [x] 下载文件(夹)



### 已实现的接口

1. 网盘基础服务
    - [x] 获取用户信息
    - [x] 获取网盘容量信息
    - [x] 获取文件信息
    - [x] 上传
    - [x] 下载
    - [ ] 创建文件夹
    - [ ] 播单能力
    - [ ] 文件分享服务(新)
    - [ ] 最近服务
    
2. ......


## Bug 反馈

- 本人编程能力有限,程序可能会有bug,如果有问题请反馈

- 如果有好的建议,也欢迎反馈 [Issues](https://github.com/zoushucai/cpanbaidu/issues)

