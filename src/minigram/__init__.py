import importlib.util

from .main import MiniGram, MiniGramMessage

__all__ = ["MiniGram", "MiniGramMessage"]

if importlib.util.find_spec("aiohttp"):
    from .aiohttp import AioMiniGram  # noqa

    __all__.append("AioMiniGram")

if importlib.util.find_spec("starlette"):
    from .starlette import StarletteMiniGram  # noqa

    __all__.append("StarletteMiniGram")
