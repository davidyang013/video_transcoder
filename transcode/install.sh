#!/bin/bash

# 检查 Homebrew 是否已安装
if ! command -v brew &> /dev/null; then
    echo "Homebrew 未安装。请访问 https://brew.sh/ 以获取安装说明。"
    echo "您可以通过运行以下命令来安装 Homebrew："
    echo "/bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    exit 1
fi

echo "Homebrew 已安装。"

# 检查 ffmpeg 是否已安装
if ! command -v ffmpeg &> /dev/null; then
    echo "ffmpeg 未安装，正在安装..."
    brew install ffmpeg
else
    echo "ffmpeg 已安装。"
fi

# 检查 ffprobe 是否已安装
if ! command -v ffprobe &> /dev/null; then
    echo "ffprobe 未安装，正在安装..."
    brew install ffmpeg
else
    echo "ffprobe 已安装。"
fi

echo "环境检查和安装完成！"