# Video Transcoder

## 功能介绍
Video Transcoder 是一个视频转码工具，支持批量转换为 H.264/AAC 格式。它可以处理多种视频格式，并提供简单易用的命令行界面。

## 安装
您可以通过以下命令安装 Video Transcoder：
python setup.py install

## 使用方法
在命令行中使用以下命令启动转码：

transcode -h
usage: transcode [-h] [-p PATH] [-s {local,global}] [-f {y,n}]

视频转码工具，支持批量将视频文件转换为 H.264/AAC 格式

options:
 -h, --help            show this help message and exit
 -p PATH, --path PATH  输入文件夹路径
 -s {local,global}, --search {local,global}
                       搜索模式
 -f {y,n}, --ffmpeg_logging {y,n}
                       控制 ffmpeg 日志输出 (y: 输出, n: 不输出)


## 配置
在使用之前，请确保安装了以下依赖：
- python 3.8

## 贡献
欢迎提交问题和贡献代码！请查看 [贡献指南](CONTRIBUTING.md) 以获取更多信息。

## 许可证
本项目采用 MIT 许可证，详情请查看 [LICENSE](LICENSE) 文件。
