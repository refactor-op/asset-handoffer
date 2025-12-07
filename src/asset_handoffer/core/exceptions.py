class HandofferError(Exception):
    pass

class ConfigError(HandofferError):
    pass

class GitError(HandofferError):
    pass

class ProcessError(HandofferError):
    pass

class ParseError(HandofferError):
    pass
