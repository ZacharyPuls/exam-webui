import pages
from nicegui import app, ui


def menu() -> None:
    for page in pages.ALL_PAGES:
        ui.link(page[0], page[1]).classes(replace="text-white")
    browser_id = app.storage.browser["id"]
    user = pages.USER_CACHE.get(browser_id, None)

    ui.space()

    if not user:
        ui.button("Login with Microsoft", on_click=lambda: ui.navigate.to("/login"))
    else:
        app.storage.user["user"] = user
        ui.button("Logout", on_click=lambda: ui.navigate.to("/logout"))
