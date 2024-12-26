from nicegui import ui

import pages


def menu() -> None:
    for page in pages.ALL_PAGES:
        ui.link(page[0], page[1]).classes(replace="text-white")
