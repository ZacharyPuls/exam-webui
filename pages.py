from nicegui import ui

from typing import List
from uuid import UUID

from style import Frame, TextLabel
import model

ALL_PAGES: frozenset[tuple[str, str]] = [["Home", "/"], ["Take Exam", "/exam"]]

TEST_RESULTS: frozenset[tuple[str, bool]] = [
    ["MPLS Fundamentals", True],
    ["MPLS L2VPN Troubleshooting", False],
]


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


@ui.refreshable
async def list_of_exam_templates() -> None:
    async def delete(exam_template: model.ExamTemplate) -> None:
        await exam_template.delete()
        list_of_exam_templates.refresh()

    exam_templates: List[model.ExamTemplate] = (
        await model.ExamTemplate.all().prefetch_related("questions")
    )

    for exam_template in reversed(exam_templates):
        with ui.card():
            with ui.row().classes("items-center"):
                ui.input("Name", on_change=exam_template.save).bind_value(
                    exam_template, "name"
                ).on("blur", list_of_exam_templates.refresh)
                ui.label().bind_text_from(
                    exam_template,
                    "num_questions",
                    backward=lambda f: f"Number of questions: {f()}",
                )
                ui.button(
                    icon="edit",
                    on_click=lambda e=exam_template: ui.navigate.to(
                        f"/admin/exam/template/{exam_template.id}"
                    ),
                )
                ui.button(
                    icon="delete",
                    on_click=lambda e=exam_template: delete(e),
                ).props("flat")


@ui.page("/admin/exam/template")
async def admin_exam_template_page() -> None:
    async def create_exam_template() -> None:
        exam_template: model.ExamTemplate = await model.ExamTemplate.create(
            name=name.value
        )
        list_of_exam_templates.refresh()
        ui.navigate.to(f"/admin/exam/template/{exam_template.id}")

    with ui.column().classes("mx-auto"):
        with ui.row().classes("w-full items-center px-4"):
            name = ui.input(label="Name")
            ui.button(on_click=create_exam_template, icon="add").props("flat").classes(
                "ml-auto"
            )
        await list_of_exam_templates()


@ui.refreshable
async def list_of_exam_template_questions() -> None:
    async def delete(exam_template_question: model.ExamTemplateQuestion) -> None:
        await exam_template_question.delete()
        list_of_exam_template_questions.refresh()

    exam_template_questions: List[model.ExamTemplateQuestion] = (
        await model.ExamTemplateQuestion.all()
    )
    for exam_template_question in reversed(exam_template_questions):
        with ui.card():
            with ui.row().classes("items-center"):
                ui.select(
                    options={t.value: t.name for t in model.QuestionType},
                    label="Type",
                    on_change=exam_template_question.save,
                ).bind_value(exam_template_question, "type").on(
                    "blur", list_of_exam_template_questions.refresh
                )
                ui.markdown("Question Body").bind_content(
                    exam_template_question, "body"
                )
                ui.button(
                    icon="delete",
                    on_click=lambda e=exam_template_question: delete(e),
                ).props("flat")


@ui.page("/admin/exam/template/{id}")
async def admin_edit_exam_template_page(id: UUID) -> None:
    async def create_exam_template_question(exam_template: model.ExamTemplate) -> None:
        await model.ExamTemplateQuestion.create(
            type=type.value, body=body.value, exam_template=exam_template
        )
        type.value = None
        body.value = ""
        list_of_exam_template_questions.refresh()

    exam_template = await model.ExamTemplate.get(id=id)
    with Frame(f"Exam Template: {exam_template.name}"):
        with ui.card():
            with ui.row().classes("items-center"):
                ui.input("Exam Name", on_change=exam_template.save).bind_value(
                    exam_template, "name"
                ).on("blur", list_of_exam_templates.refresh)
            ui.separator()
            ui.label("Exam Questions:")
            with ui.row().classes("w-full items-center px-4"):
                type = ui.select(
                    options={t.value: t.name for t in model.QuestionType}, label="Type"
                )
                body = ui.editor(placeholder="Question Body")
                ui.button(
                    icon="add",
                    on_click=lambda e=exam_template: create_exam_template_question(e),
                ).props("flat").classes("ml-auto")
            with ui.row().classes("items-center"):
                await list_of_exam_template_questions()
