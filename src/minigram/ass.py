import asyncio
import functools
import inspect


def ass(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        signature = inspect.signature(func).parameters
        try:
            loop = asyncio.get_running_loop()
            if "is_async" in signature:
                kwargs["is_async"] = True
            return func(*args, **kwargs)
        except RuntimeError:
            if "is_async" in signature:
                kwargs["is_async"] = False
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(func(*args, **kwargs))
            loop.close()
            return result

    return wrapper
