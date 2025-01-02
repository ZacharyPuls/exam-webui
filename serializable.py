"""
Copyright 2024, Kansas Fiber Network, LLC

:author: Zach Puls <zpuls@ksfiber.net>
"""


class Serializable:
    """Helper class for objects being persisted to/from a database"""

    async def new(self) -> None:
        pass

    async def save(self) -> None:
        pass

    @staticmethod
    async def load(from_value: any) -> any:
        pass
