"""Asset Handoffer - 资产交接自动化工具

让美术零成本提交资产到GitHub。

核心特性：
- 不需要学习Git
- 不需要安装Unity  
- 只需要拖文件+一个命令


"""

__version__ = "0.9.11"
__author__ = "Refactor"
__email__ = "refactor.op@gmail.com"

# 导出核心类
from .core.config import Config
from .core.git_repo import GitRepo
from .core.processor import FileProcessor
from .parsers import FilenameParser, ParsedFilename


# 导出异常
from .exceptions import (
    HandofferError,
    ConfigError,
    GitError,
    ProcessError,
    ParseError,
)

__all__ = [
    # 版本信息
    '__version__',
    '__author__',
    '__email__',
    
    # 核心类
    'Config',
    'GitRepo',
    'FileProcessor',
    'FilenameParser',
    
    # 数据模型
    'ParsedFilename',
    
    # 异常
    'HandofferError',
    'ConfigError',
    'GitError',
    'ProcessError',
    'ParseError',
]
