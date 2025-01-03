"""
Copyright 2024, Kansas Fiber Network, LLC

:author: Zach Puls <zpuls@ksfiber.net>
"""

from dataclasses import dataclass, field
from typing import List
from user import User
from uuid import UUID

import model

from nicegui import ui

from serializable import Serializable


@dataclass
class ExamTemplateQuestionResponse(Serializable):

    id: UUID
    exam_template_question_id: UUID
    value: str
    is_correct: bool

    async def new(self) -> None:
        exam_template_question_response = (
            await model.ExamTemplateQuestionResponse.create(
                exam_template_question_id=self.exam_template_question_id,
                value=self.value,
                is_correct=False,
            )
        )
        self.id = exam_template_question_response.id
        self.edit.refresh()

    async def save(self) -> None:
        exam_template_question_response = await model.ExamTemplateQuestionResponse.get(
            id=self.id
        )
        exam_template_question_response.value = self.value
        exam_template_question_response.is_correct = self.is_correct
        await exam_template_question_response.save()
        self.edit.refresh()

    async def delete(self) -> None:
        response = await model.ExamTemplateQuestionResponse.get(id=self.id)
        await response.delete()
        self.id = None
        self.exam_template_question_id = None
        self.value = None

    @staticmethod
    async def load(from_value: model.ExamTemplateQuestionResponse) -> any:
        return ExamTemplateQuestionResponse(
            id=from_value.id,
            exam_template_question_id=from_value.id,
            value=from_value.value,
            is_correct=from_value.is_correct,
        )

    @ui.refreshable
    async def edit(self) -> None:
        ui.input().on(type="blur", handler=self.save).bind_value(
            self, "value"
        ).tailwind.background_color("green-800" if self.is_correct else "")


@dataclass
class ExamTemplateQuestion(Serializable):

    id: UUID
    exam_template_id: UUID
    type: model.QuestionType
    body: str
    responses: List[ExamTemplateQuestionResponse] = field(default_factory=lambda: [])

    async def new(self) -> None:
        exam_template_question = await model.ExamTemplateQuestion.create(
            exam_template_id=self.exam_template_id,
            type=self.type,
            body=self.body,
        )
        self.id = exam_template_question.id
        for response in self.responses:
            response.exam_template_question_id = self.id
            response.new()

    async def save(self) -> None:
        question = await model.ExamTemplateQuestion.get(id=self.id)
        question.type = self.type
        question.body = self.body
        await question.save()
        for response in self.responses:
            await response.save()
        self.edit.refresh()

    async def delete(self) -> None:
        for response in self.responses:
            await response.delete()
        question = await model.ExamTemplateQuestion.get(id=self.id)
        await question.delete()
        self.id = None
        self.exam_template_id = None
        self.type = None
        self.body = None
        self.responses.clear()

    async def add_response(self, response: ExamTemplateQuestionResponse) -> None:
        self.responses.append(response)
        await response.new()
        self.edit.refresh()

    async def delete_response(self, response: ExamTemplateQuestionResponse) -> None:
        self.responses.remove(response)
        await response.delete()
        self.edit.refresh()

    async def toggle_response_correct(
        self, response: ExamTemplateQuestionResponse
    ) -> None:
        response.is_correct = not response.is_correct
        await response.save()
        self.edit.refresh()

    @staticmethod
    async def load(from_value: model.ExamTemplateQuestion) -> any:
        exam_template_id = from_value.exam_template.id
        exam_template_question = ExamTemplateQuestion(
            id=from_value.id,
            exam_template_id=exam_template_id,
            type=from_value.type,
            body=from_value.body,
            responses=[],
        )
        for response in from_value.responses:
            exam_template_question.responses.append(
                await ExamTemplateQuestionResponse.load(response)
            )
        return exam_template_question

    @ui.refreshable
    async def create(self) -> None:
        if not self.id:
            exam_template_question = await model.ExamTemplateQuestion.create(
                exam_template_id=self.exam_template_id, type=self.type, body=self.body
            )
            self.id = exam_template_question.id
        new_response = ExamTemplateQuestionResponse(
            id=None, exam_template_question_id=self.id, value="", is_correct=False
        )
        with ui.row():
            ui.select(
                options={t.value: t.name for t in model.QuestionType}, label="Type"
            ).on_value_change(self.new).bind_value(self, "type")
            ui.editor(placeholder="Question Body").on_value_change(self.new).bind_value(
                self, "body"
            )
            with ui.column():
                with ui.row():
                    ui.input().bind_value(new_response, "value")
                    ui.button(
                        on_click=lambda: self.add_response(new_response), icon="add"
                    ).props("flat")
                for response in reversed(self.responses):
                    await response.edit()
            ui.button(on_click=self.new, icon="save").props("flat")

    @ui.refreshable
    async def edit(self) -> None:
        if not self.id:
            exam_template_question = await model.ExamTemplateQuestion.create(
                exam_template_id=self.exam_template_id,
                type=self.type,
                body=self.body,
            )
            self.id = exam_template_question.id
        new_response = ExamTemplateQuestionResponse(
            id=None, exam_template_question_id=self.id, value="", is_correct=False
        )

        ui.select(
            options={t.value: t.name for t in model.QuestionType}, label="Type"
        ).on(type="blur", handler=self.save).bind_value(self, "type")
        ui.editor(placeholder="Question Body").on(
            type="blur", handler=self.save
        ).bind_value(self, "body")
        with ui.column():
            with ui.row():
                ui.input().bind_value(new_response, "value")
                ui.button(
                    on_click=lambda: self.add_response(new_response), icon="add"
                ).props("flat").classes("ml-auto")
            for response in reversed(self.responses):
                with ui.row():
                    await response.edit()
                    ui.button(
                        on_click=lambda r=response: self.toggle_response_correct(r),
                        icon="check",
                    )
                    ui.button(
                        on_click=lambda r=response: self.delete_response(r),
                        icon="delete",
                    ).props("flat").classes("ml-auto")


@dataclass
class ExamTemplate(Serializable):

    id: UUID
    name: str
    questions: List[ExamTemplateQuestion] = field(default_factory=lambda: [])

    selected_question: int = 1

    async def new(self) -> None:
        author = await User.get_active()
        exam_template = await model.ExamTemplate.create(
            name=self.name, author=author, updated_by=author
        )
        self.id = exam_template.id
        self.create.refresh()
        ui.navigate.to(f"/admin/exam/template/{exam_template.id}")

    async def save(self) -> None:
        exam_template = await model.ExamTemplate.get(id=self.id)
        exam_template.name = self.name
        exam_template.updated_by = await User.get_active()
        await exam_template.save()

        for question in self.questions:
            await question.save()
        self.edit.refresh()

    @staticmethod
    async def load(from_value: model.ExamTemplate) -> any:
        exam_template = ExamTemplate(id=from_value.id, name=from_value.name)
        for question in from_value.questions:
            exam_template.questions.append(await ExamTemplateQuestion.load(question))
        return exam_template

    async def add_question(self) -> None:
        new_question = ExamTemplateQuestion(
            id=None,
            exam_template_id=self.id,
            type=model.QuestionType.MULTIPLE_CHOICE_SINGLE_SELECT,
            body="",
        )
        await new_question.new()
        self.questions.append(new_question)
        await self.save()
        self.edit_card.refresh()

    async def delete_question(self, question: ExamTemplateQuestion) -> None:
        self.questions.remove(question)
        await question.delete()
        await self.save()
        self.selected_question = 1
        self.edit_card.refresh()

    @ui.refreshable
    async def create(self) -> None:
        with ui.card():
            with ui.row():
                ui.input(label="Name").bind_value(self, "name")
                ui.button(on_click=self.new, icon="add").props("flat")

    # Inner Edit card is separated into its own method to allow refreshing without breaking pagination

    @ui.refreshable
    async def edit_card(self) -> None:
        question = self.questions[self.selected_question - 1]
        with ui.card():
            with ui.card_actions().classes("w-full justify-end"):
                ui.button(
                    on_click=lambda q=question: self.delete_question(q),
                    icon="close",
                )
            with ui.row():
                await question.edit()

    @ui.refreshable
    async def edit(self) -> None:
        with ui.card().classes("absolute-center items-center w-full mx-auto"):
            with ui.card_section():
                ui.input("Exam Name").on(type="blur", handler=self.save).bind_value(
                    self, "name"
                )
                ui.button(text="Add Question", on_click=self.add_question).props("flat")
            ui.separator()
            with ui.card_section():
                with ui.row():
                    ui.pagination(
                        1,
                        len(self.questions),
                        direction_links=True,
                        on_change=self.edit_card.refresh,
                    ).classes("mx-auto").bind_value(self, "selected_question")
                await self.edit_card()

    @ui.refreshable
    async def summary(self) -> None:
        with ui.card():
            with ui.row():
                ui.label("Exam Name: ")
                ui.label().bind_text_from(self, "name")
            with ui.row():
                ui.label("Number of Questions: ")
                ui.label().bind_text_from(self, "questions", backward=len)
            with ui.card_actions():
                ui.button(
                    icon="edit",
                    on_click=lambda: ui.navigate.to(f"/admin/exam/template/{self.id}"),
                )
