import pages
from fastapi import Request
from nicegui import app, ui


def redirect_to_login_page(request: Request) -> None:
    app.storage.user["previous_url"] = request.url.path
    ui.navigate.to("/login")


def menu(request: Request) -> None:
    for page in pages.ALL_PAGES:
        ui.link(page[0], page[1]).classes(replace="text-white")
    browser_id = app.storage.browser["id"]
    user = pages.USER_CACHE.get(browser_id, None)

    ui.space()

    if not user:
        ui.button(
            "Login with Microsoft", on_click=lambda r=request: redirect_to_login_page(r)
        )
    else:
        app.storage.user["user"] = user
        ui.button("Logout", on_click=lambda: ui.navigate.to("/logout"))
