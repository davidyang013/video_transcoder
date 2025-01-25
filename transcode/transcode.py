#!/usr/bin/env python3
"""
视频转码工具
支持批量将视频文件转换为 H.264/AAC 格式
"""

import os
import sys
import json
import logging
import subprocess
import time  # 导入 time 模块
from typing import Optional, Dict, Any, List
from pathlib import Path
import configparser
import argparse  # 导入 argparse 模块
import math  # 导入 math 模块

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 默认支持的视频格式
DEFAULT_SUPPORTED_FORMATS = (
    '.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v',
    '.mp3', '.wav', '.aac', '.m4a', '.wma', '.ts', '.mts', '.m2ts', '.vob', '.3gp'
)

CONFIG_FILE = "config.ini"
CHUNK_SIZE_MB = 100  # 每个切割文件的大小（MB）

def create_config_file():
    """创建 config.ini 文件并写入默认支持的视频格式"""
    config = configparser.ConfigParser()
    config['Formats'] = {
        'supported_formats': ', '.join(DEFAULT_SUPPORTED_FORMATS)
    }
    with open(CONFIG_FILE, 'w') as configfile:
        config.write(configfile)
    logger.info(f"Created config file: {CONFIG_FILE} with default formats.")

def load_supported_formats(config_file: str) -> List[str]:
    """从配置文件加载支持的视频格式"""
    config = configparser.ConfigParser()
    if os.path.exists(config_file):
        config.read(config_file)
        if 'Formats' in config and 'supported_formats' in config['Formats']:
            formats = config['Formats']['supported_formats']
            return [fmt.strip() for fmt in formats.split(',')]
    return list(DEFAULT_SUPPORTED_FORMATS)

class VideoTranscoder:
    def __init__(self, directory: str, search_mode: str, supported_formats: List[str], ffmpeg_logging: bool):
        self.directory = Path(directory)
        self.search_mode = search_mode
        self.supported_formats = supported_formats
        self.ffmpeg_logging = ffmpeg_logging  # 控制 ffmpeg 日志输出

    def get_video_info(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """获取视频文件信息"""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', 
                '-print_format', 'json',
                '-show_format', '-show_streams', 
                str(file_path)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            logger.error(f"Error getting video info for {file_path}: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing video info for {file_path}: {e}")
            return None

    def split_video(self, input_path: Path, duration: float, size_mb: float) -> List[Path]:
        """将视频文件切割为多个小文件"""
        logger.info(f"Splitting video {input_path.name} into chunks based on duration and size.")
        
        # 计算切分个数
        num_chunks = math.ceil(size_mb / CHUNK_SIZE_MB)  # 向上取整
        logger.info(f"Calculated number of chunks: {num_chunks}")

        chunk_files = []
        for i in range(num_chunks):
            start_time = i * (duration / num_chunks)  # 每个切割文件的起始时间（秒）
            chunk_file = input_path.with_name(f"{input_path.stem}_part{i + 1}.mp4")
            cmd = [
                'ffmpeg', '-i', str(input_path),
                '-ss', str(start_time),  # 从指定位置开始切割
                '-t', str(duration / num_chunks),  # 切割指定时长（秒）
                '-c', 'copy',  # 直接复制，不重新编码
                str(chunk_file)
            ]
            if not self.ffmpeg_logging:
                cmd.append('-loglevel')
                cmd.append('quiet')

            logger.info(f"Executing split command: {' '.join(cmd)}")
            subprocess.run(cmd, check=True)
            chunk_files.append(chunk_file)
            logger.info(f"Created chunk: {chunk_file.name}")

        return chunk_files

    def transcode_chunk(self, chunk_file: Path) -> Path:
        """转码切割后的视频文件"""
        output_path = chunk_file.with_name(f"{chunk_file.stem}..mp4")  # 输出文件名加上 "..mp4"
        logger.info(f"Starting transcoding for chunk {chunk_file.name} to {output_path.name}")
        cmd = [
            'ffmpeg', '-i', str(chunk_file),
            '-c:v', 'libx264', '-preset', 'medium',
            '-crf', '23', '-c:a', 'aac',
            '-strict', '2', '-b:a', '128k',
            '-movflags', '+faststart', '-y', str(output_path)
        ]
        
        # 控制 ffmpeg 日志输出
        if not self.ffmpeg_logging:
            cmd.append('-loglevel')
            cmd.append('quiet')

        logger.info(f"Executing command: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
        logger.info(f"Transcoding completed for chunk {chunk_file.name}")

        # 删除原始切割文件
        chunk_file.unlink()  # 删除原始切割文件
        logger.info(f"Deleted original chunk file: {chunk_file.name}")

        return output_path

    def merge_videos(self, chunk_files: List[Path], original_file: Path) -> None:
        """合并切割后的视频文件"""
        output_path = original_file.with_name(f"{original_file.stem}..mp4")  # 使用原始文件名，无后缀，加上 "..mp4"
        logger.info(f"Merging {len(chunk_files)} chunks into {output_path.name}.")
        with open("file_list.txt", "w") as f:
            for chunk in chunk_files:
                f.write(f"file '{chunk}'\n")

        cmd = ['ffmpeg', '-f', 'concat', '-safe', '0', '-i', 'file_list.txt', '-c', 'copy', str(output_path)]
        if not self.ffmpeg_logging:
            cmd.append('-loglevel')
            cmd.append('quiet')

        logger.info(f"Executing merge command: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
        logger.info(f"Merged video created: {output_path.name}")

        # 删除中间文件
        for chunk in chunk_files:
            chunk.unlink()  # 删除原始切割文件
            logger.info(f"Deleted original chunk file: {chunk.name}")
        os.remove("file_list.txt")  # 删除文件列表

        # 删除原始文件
        original_file.unlink()  # 删除最开始的原始文件
        logger.info(f"Deleted original video file: {original_file.name}")

    def transcode_video(self, input_path: Path) -> bool:
        """转码视频文件为 MP4 格式"""
        try:
            # 获取视频信息
            video_info = self.get_video_info(input_path)
            if video_info:
                # 提取并打印视频信息
                duration = float(video_info['format']['duration'])
                format_name = video_info['format']['format_name']
                size_bytes = int(video_info['format']['size'])  # 文件大小（字节）
                size_mb = size_bytes / (1024 * 1024)  # 转换为 MB
                
                logger.info(f"Video Info for {input_path.name}:")
                logger.info(f"  Duration: {duration} seconds")
                logger.info(f"  Format: {format_name}")
                logger.info(f"  Size: {size_mb:.2f} MB")  # 输出为 MB，保留两位小数

            # 判断文件大小，决定是否切割
            if size_mb > CHUNK_SIZE_MB:
                chunk_files = self.split_video(input_path, duration, size_mb)  # 切割视频
                transcoded_chunks = [self.transcode_chunk(chunk) for chunk in chunk_files]  # 转换每个切割文件
                self.merge_videos(transcoded_chunks, input_path)  # 合并切割后的视频
            else:
                # 生成新的输出文件名
                output_path = input_path.with_name(f"{input_path.stem}..mp4")  # 输出文件名加上 "..mp4"
                
                logger.info(f"Starting transcoding for {input_path} to {output_path}")
                cmd = [
                    'ffmpeg', '-i', str(input_path),
                    '-c:v', 'libx264', '-preset', 'medium',
                    '-crf', '23', '-c:a', 'aac',
                    '-strict', '2', '-b:a', '128k',
                    '-movflags', '+faststart', '-y', str(output_path)
                ]
                
                # 控制 ffmpeg 日志输出
                if not self.ffmpeg_logging:
                    cmd.append('-loglevel')
                    cmd.append('quiet')

                # 输出 ffmpeg 命令到日志
                logger.info(f"Executing command: {' '.join(cmd)}")
                
                # 使用 Popen 执行命令并实时输出日志
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                for line in process.stdout:
                    logger.info(f"FFmpeg output: {line.strip()}")
                stderr_output = process.stderr.read()
                if stderr_output:
                    logger.error(f"FFmpeg error output: {stderr_output.strip()}")
                
                process.wait()  # 等待进程结束
                
                logger.info(f"Transcoding completed for {input_path}")
                
                # 检查输出文件是否创建成功
                if output_path.exists() and output_path.stat().st_size > 0:
                    return True
                else:
                    logger.error(f"Output file is empty or not created: {output_path}")
                    return False
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Transcoding error for {input_path}: {e}")
            logger.error(f"FFmpeg error output: {e.stderr}")  # 输出 ffmpeg 错误信息
            return False
        except Exception as e:
            logger.error(f"Unexpected error while transcoding {input_path}: {e}")
            return False

    def process_directory(self) -> None:
        """处理目录中的所有支持格式的文件并转换为 MP4"""
        if not self.directory.exists():
            logger.error(f"Input directory does not exist: {self.directory}")
            sys.exit(1)

        # 获取待处理文件列表
        files_to_process = list(self.directory.glob('*')) if self.search_mode == 'local' else list(self.directory.rglob('*'))

        # 过滤掉以 ._ 开头的文件
        files_to_process = [f for f in files_to_process if not f.name.startswith('._')]
        
        # 只统计需要转换的文件
        files_to_convert = [f for f in files_to_process if f.suffix.lower() in self.supported_formats and not f.name.endswith("..mp4")]
        total_files = len(files_to_convert)

        if total_files == 0:
            logger.info("No files to process in the specified directory.")
            return

        successful_conversions = 0
        failed_conversions = 0

        for index, input_path in enumerate(files_to_convert, start=1):
            logger.info(f"Processing file {index}/{total_files}: {input_path.name}")
            
            # 转码文件
            if self.transcode_video(input_path):
                successful_conversions += 1
                # 删除原始文件
                input_path.unlink()
                logger.info(f"Deleted original file: {input_path}")
            else:
                failed_conversions += 1

            # 输出整体进度
            logger.info(f"Progress: {successful_conversions + failed_conversions}/{total_files} files processed.")

        # 输出统计信息
        logger.info(f"\nConversion Summary:")
        logger.info(f"Total files processed: {total_files}")
        logger.info(f"Successfully converted: {successful_conversions}")
        logger.info(f"Failed conversions: {failed_conversions}")

def check_dependencies() -> bool:
    """检查必要的依赖是否已安装"""
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        subprocess.run(['ffprobe', '-version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        logger.error(f"Dependency check failed: {e}")
        return False

def main():
    """主函数"""
    # 设置命令行参数解析
    parser = argparse.ArgumentParser(description='视频转码工具，支持批量将视频文件转换为 H.264/AAC 格式')
    parser.add_argument('-p', '--path', type=str, default=os.path.expanduser("~/Movies/bgm"), help='输入文件夹路径')
    parser.add_argument('-s', '--search', type=str, choices=['local', 'global'], default='local', help='搜索模式')
    parser.add_argument('-f', '--ffmpeg_logging', type=str, choices=['y', 'n'], default='n', help='控制 ffmpeg 日志输出 (y: 输出, n: 不输出)')
    
    args = parser.parse_args()

    # 检查输入路径是否存在
    if not os.path.exists(args.path):
        print(f"错误: 输入路径不存在: {args.path}")
        sys.exit(1)

    # 检查必要的依赖
    if not check_dependencies():
        logger.error("ffmpeg 和 ffprobe 是必需的，但未安装。")
        logger.error("请运行: ./install.sh 来安装依赖")
        sys.exit(1)

    # 开始计时
    start_time = time.time()

    # 创建 VideoTranscoder 实例并处理目录
    ffmpeg_logging = args.ffmpeg_logging == 'y'  # 将 'y' 转换为布尔值
    transcoder = VideoTranscoder(args.path, args.search, load_supported_formats(CONFIG_FILE), ffmpeg_logging)
    transcoder.process_directory()

    # 结束计时
    end_time = time.time()
    elapsed_time = end_time - start_time
    logger.info(f"Total time taken for transcoding: {elapsed_time:.2f} seconds")

    print("转码完成！请检查输出目录。")

if __name__ == "__main__":
    main()
