"""
Asset Handoffer
"""

__version__ = "0.10.2"
__author__ = "Refactor"
__email__ = "refactor.op@gmail.com"

from .core import *  # noqa: F401, F403
from .core import __all__ as _core_all

__all__ = ['__version__', '__author__', '__email__']
__all__.extend(_core_all)
