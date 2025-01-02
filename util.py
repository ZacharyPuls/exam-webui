"""
Copyright 2024, Kansas Fiber Network, LLC

:author: Zach Puls <zpuls@ksfiber.net>
"""

# Pulled from https://stackoverflow.com/a/45364670


class aobject(object):
    """Inheriting this class allows you to define an async __init__.

    So you can create objects by doing something like `await MyClass(params)`
    """

    async def __new__(cls, *a, **kw):
        instance = super().__new__(cls)
        await instance.__init__(*a, **kw)
        return instance

    async def __init__(self):
        pass
