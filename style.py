from contextlib import contextmanager

from menu import menu
from nicegui import ui


class TextLabel(ui.label):
    def __init__(self, text: str) -> None:
        super().__init__(text)
        self.classes("text-h4 text-grey-8")


@contextmanager
def Frame(navigation_title: str):
    """Custom page frame to share the same styling and behavior across all pages"""
    ui.colors(
        primary="#6E93D6", secondary="#53B689", accent="#111B1E", positive="#53B689"
    )
    with ui.header():
        ui.label("KFN Exam Platform").classes("font-bold")
        ui.space()
        ui.label(navigation_title)
        ui.space()
        with ui.row():
            menu()
    yield
