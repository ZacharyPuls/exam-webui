from typing import List
from uuid import UUID

import config
import jwt
import model

import msal

import requests

from admin.exam_template import ExamTemplate
from cachetools import TTLCache
from fastapi import Request
from fastapi.responses import RedirectResponse

from jwt.algorithms import RSAAlgorithm
from nicegui import app, Client, ui

from style import Frame, TextLabel

ALL_PAGES: frozenset[tuple[str, str]] = [["Home", "/"], ["Take Exam", "/exam"]]

TEST_RESULTS: frozenset[tuple[str, bool]] = [
    ["MPLS Fundamentals", True],
    ["MPLS L2VPN Troubleshooting", False],
]

INPROGRESS_AUTH_FLOW_CACHE = TTLCache(maxsize=10, ttl=60 * 5)
USER_CACHE = TTLCache(maxsize=100, ttl=60 * 60 * 10)

msal_application = msal.ConfidentialClientApplication(
    client_id=config.ENTRA_CLIENT_ID,
    client_credential=config.ENTRA_CLIENT_SECRET,
    authority=config.ENTRA_AUTHORITY,
)


@ui.page("/login")
async def login_page(request: Request) -> None:
    auth_flow = msal_application.initiate_auth_code_flow(
        scopes=config.ENTRA_APPLICATION_SCOPE,
        redirect_uri=f"{str(request.base_url).rstrip("/")}{config.OAUTH_REDIRECT_URI}",
    )
    browser_id = app.storage.browser["id"]
    INPROGRESS_AUTH_FLOW_CACHE[browser_id] = auth_flow

    return RedirectResponse(auth_flow["auth_uri"])


def get_tenant_public_key(key_id: str) -> str:
    jwks_json = requests.get(config.ENTRA_JWKS_URL, timeout=60).json()

    key = next((key for key in jwks_json["keys"] if key["kid"] == key_id), None)

    if key:
        return RSAAlgorithm.from_jwk(key)
    raise RuntimeError(
        f"[get_tenant_public_key] Public key not found for key_id: {key_id}"
    )


def validate_and_decode_jwt_token(jwt_token: str) -> str:
    jwt_header = jwt.get_unverified_header(jwt_token)
    public_key = get_tenant_public_key(jwt_header["kid"])
    return jwt.decode(
        jwt_token,
        public_key,
        algorithms=[jwt_header["alg"]],
        audience=config.ENTRA_CLIENT_ID,
    )


@ui.page(config.OAUTH_REDIRECT_URI)
async def oauth_redirect_page(client: Client) -> None:
    browser_id = app.storage.browser["id"]
    auth_flow = INPROGRESS_AUTH_FLOW_CACHE.get(browser_id, None)

    if auth_flow is None:
        return ui.navigate.to("/login")
    auth_state = client.request.query_params["state"]

    if auth_state != auth_flow["state"]:
        ui.label(
            f"Error during Entra AD authentication - Invalid auth_state parameter: {auth_state} != {auth_flow["state"]}"
        )
        return
    query_params = dict(client.request.query_params)
    auth_token = msal_application.acquire_token_by_auth_code_flow(
        auth_flow, query_params
    )

    if "error" in auth_token:
        ui.label(
            f"Error during Entra AD authentication - {auth_token["error"]}: {auth_token["error_description"]}"
        )
        return
    id_token = auth_token.get("id_token")
    claims = validate_and_decode_jwt_token(id_token)

    if not claims:
        ui.label(f"Error during Entra AD authentication - Invalid ID token: {id_token}")
        return
    USER_CACHE[browser_id] = claims

    ui.navigate.to("/")


@ui.page("/logout")
def logout_page(request: Request):
    browser_id = app.storage.browser["id"]

    if browser_id in INPROGRESS_AUTH_FLOW_CACHE:
        del INPROGRESS_AUTH_FLOW_CACHE[browser_id]
    if browser_id in USER_CACHE:
        del USER_CACHE[browser_id]
    if "user" in app.storage.user:
        del app.storage.user["user"]
    return RedirectResponse(
        f"{config.ENTRA_LOGOUT_ENDPOINT}?post_logout_redirect_uri={request.base_url}"
    )


@ui.page("/")
async def index_page() -> None:
    with Frame("Home"):
        TextLabel("Your assigned exams: ").classes("font-bold")
        ui.separator()
        with ui.grid(columns=3):
            for result in TEST_RESULTS:
                TextLabel(result[0])
                TextLabel("Result: ")
                TextLabel("PASS" if result[1] else "FAIL")


@ui.page("/exam")
async def exam_index_page() -> None:
    with Frame("- Exam -"):
        TextLabel("Exam")
        ui.label("This is the exam index page.")


@ui.page("/exam/{id}")
async def exam_page(id: UUID) -> None:
    async def start_exam(exam: model.Exam):
        print(f"Starting exam: {exam.name}")
        first_question = await exam.questions.all().first().prefetch_related("response")
        ui.navigate.to(f"/exam/{exam.id}/question/{first_question.id}")

    with await model.Exam.get(id=id).prefetch_related("questions") as exam:
        with Frame(f"Exam: {exam.name}"):
            with ui.card():
                with ui.row().classes("items-center"):
                    TextLabel(f"Press to start exam: ")
                    ui.button(icon="play", on_click=lambda e=exam: start_exam(e)).props(
                        "flat"
                    )


@ui.page("/exam/{exam_id}/question/{question_id}")
async def exam_question_page(exam_id: UUID, question_id: UUID) -> None:
    with await model.ExamQuestion.get(
        id=question_id
    ) as exam_question, await model.Exam.get(id=exam_id) as exam:
        with Frame(f"Exam: {exam.name} - Question {question_id}"):
            with ui.card():
                with ui.row().classes("items-center"):
                    ui.markdown().bind_content_from(exam_question, "body")
                with ui.row().classes("items-center"):
                    ui.editor(placeholder="Answer")


@ui.refreshable
async def list_of_users() -> None:
    async def delete(user: model.User) -> None:
        await user.delete()
        list_of_users.refresh()

    users: List[model.User] = await model.User.all()
    for user in reversed(users):
        with ui.card():
            with ui.row().classes("items-center"):
                ui.input("Name", on_change=user.save).bind_value(user, "name").on(
                    "blur", list_of_users.refresh
                )
                ui.input("Email", on_change=user.save).bind_value(user, "email").on(
                    "blur", list_of_users.refresh
                )
                ui.button(icon="delete", on_click=lambda u=user: delete(u)).props(
                    "flat"
                )


@ui.page("/admin/user")
async def admin_user_page() -> None:
    async def create_user() -> None:
        await model.User.create(name=name.value, email=email.value)
        name.value = ""
        email.value = ""
        list_of_users.refresh()

    with ui.column().classes("mx-auto"):
        with ui.row().classes("w-full items-center px-4"):
            name = ui.input(label="Name")
            email = ui.input(label="Email")
            ui.button(on_click=create_user, icon="add").props("flat").classes("ml-auto")
        await list_of_users()


@ui.refreshable
async def list_of_active_exams() -> None:
    async def cancel(exam: model.Exam) -> None:
        # TODO: do we want to actually delete it? Or just flag it as cancelled?

        await exam.delete()
        list_of_active_exams.refresh()

    active_exams: List[model.Exam] = await model.Exam.filter(
        is_complete=False
    ).prefetch_related("questions")

    for exam in reversed(active_exams):
        with ui.card():
            with ui.row().classes("items-center"):
                ui.label().bind_text_from(
                    exam.user, "name", backward=lambda n: f"Assigned User: {n}"
                )
                ui.button(icon="close", on_click=lambda e=exam: cancel(exam))


@ui.page("/admin/exam/")
async def admin_exam_page() -> None:
    async def assign_exam_to_user() -> None:
        exam: model.Exam = await model.Exam.create(
            user=user.value, name=exam_template.value, is_complete=False
        )
        for exam_question in exam_template.value.questions:
            await model.ExamQuestion.create(
                exam=exam, type=exam_question.type, body=exam_question.body
            )
        list_of_active_exams.refresh()

    all_users: List[model.User] = await model.User.all()
    all_exam_templates: List[model.ExamTemplate] = (
        await model.ExamTemplate.all().prefetch_related("questions")
    )

    with ui.column().classes("mx-auto"):
        with ui.row().classes("w-full items-center px-4"):
            user = ui.select(options={u: u.name for u in all_users}, label="User")
            exam_template = ui.select(
                options={e: e.name for e in all_exam_templates},
                label="Exam to assign",
            )
            ui.button(on_click=assign_exam_to_user, icon="add").props("flat").classes(
                "ml-auto"
            )
        await list_of_active_exams()


@ui.page("/admin/exam/template")
async def admin_exam_template_page() -> None:
    exam_template = ExamTemplate(id=None, name=None)
    await exam_template.create()


@ui.page("/admin/exam/template/{id}")
async def admin_edit_exam_template_page(id: UUID) -> None:
    with Frame("Admin - Edit Exam Template"):
        exam_template: model.ExamTemplate = await ExamTemplate.load(
            await model.ExamTemplate.get(id=id).prefetch_related(
                "questions",
                "questions__responses",
                "questions__exam_template",
                "questions__responses__exam_template_question",
            )
        )
        await exam_template.edit()
