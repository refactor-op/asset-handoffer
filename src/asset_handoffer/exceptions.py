"""异常体系

所有自定义异常，替代 sys.exit() 的使用。
使得核心库可以被嵌入到其他应用中。
"""


class HandofferError(Exception):
    """Asset Handoffer 基础异常类"""
    pass


class ConfigError(HandofferError):
    """配置错误"""
    pass


class GitError(HandofferError):
    """Git 操作错误"""
    pass


class ProcessError(HandofferError):
    """文件处理错误"""
    pass


class ParseError(HandofferError):
    """文件名解析错误"""
    pass
