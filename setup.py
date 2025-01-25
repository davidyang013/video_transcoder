from setuptools import setup, find_packages

setup(
    name='video_transcoder',  # 包名
    version='0.1.0',  # 版本号
    author='David Y',  # 作者
    author_email='davidyang013@gmail.com',  # 作者邮箱
    description='A video transcoding tool that supports batch conversion to H.264/AAC format.',  # 简短描述
    long_description=open('README.md').read(),  # 长描述，通常从 README 文件中读取
    long_description_content_type='text/markdown',  # 长描述的内容类型
    url='https://github.com/davidyang013/video_transcoder',  # 项目主页
    packages=find_packages(),  # 自动查找包
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',  # Python 版本要求
    install_requires=[
        'ffmpeg-python',  # 依赖包
        # 在这里添加其他依赖
    ],
    entry_points={
        'console_scripts': [
            'transcode=transcode.transcode:main',  # 命令行入口
        ],
    },
)
