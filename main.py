from nicegui import app, ui
from tortoise import Tortoise

from pages import *


async def init_db() -> None:
    await Tortoise.init(db_url="sqlite://db.sqlite3", modules={"model": ["model"]})
    await Tortoise.generate_schemas()


async def deinit_db() -> None:
    await Tortoise.close_connections()


def main() -> None:
    app.on_startup(init_db)
    app.on_shutdown(deinit_db)
    ui.run(
        title="KFN Exam Platform",
        host="127.0.0.1",
        dark=None,
        storage_secret=config.NICEGUI_STORAGE_SECRET,
    )


if __name__ in {"__main__", "__mp_main__"}:
    main()
