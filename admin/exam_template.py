"""
Copyright 2024, Kansas Fiber Network, LLC

:author: Zach Puls <zpuls@ksfiber.net>
"""

from dataclasses import dataclass, field
from typing import List
from uuid import UUID

import model

from nicegui import ui

from serializable import Serializable


@dataclass
class ExamTemplateQuestionResponse(Serializable):

    id: UUID
    exam_template_question_id: UUID
    value: str

    async def new(self) -> None:
        exam_template_question_response = (
            await model.ExamTemplateQuestionResponse.create(
                exam_template_question_id=self.exam_template_question_id,
                value=self.value,
            )
        )
        self.id = exam_template_question_response.id
        self.create.refresh()

    async def save(self) -> None:
        await model.ExamTemplateQuestionResponse.update_or_create(
            id=self.id,
            exam_template_question_id=self.exam_template_question_id,
            value=self.value,
        )
        self.edit.refresh()

    @staticmethod
    async def load(from_value: model.ExamTemplateQuestionResponse) -> any:
        return ExamTemplateQuestionResponse(
            id=from_value.id,
            exam_template_question_id=from_value.exam_template_question.id,
            value=from_value.value,
        )

    @ui.refreshable
    async def create(self) -> None:
        with ui.row():
            ui.input().bind_value(self, "value")
            ui.button(on_click=self.new, icon="add").props("flat")

    @ui.refreshable
    async def edit(self) -> None:
        with ui.row():
            ui.input().bind_value(self, "value")
            ui.button(on_click=self.save, icon="save").props("flat")


@dataclass
class ExamTemplateQuestion(Serializable):

    id: UUID
    exam_template_id: UUID
    type: model.QuestionType
    body: str
    responses: List[ExamTemplateQuestionResponse] = field(default_factory=lambda: [])

    async def new(self) -> None:
        exam_template_question = await model.ExamTemplateQuestion.create(
            exam_template_id=self.exam_template_id, type=self.type, body=self.body
        )
        self.id = exam_template_question.id
        for response in self.responses:
            if response.exam_template_question_id is None:
                response.exam_template_question_id = self.id
            response.new()
        self.create.refresh()

    async def save(self) -> None:
        await model.ExamTemplateQuestion.update_or_create(
            id=self.id, type=self.type, body=self.body
        )
        for response in self.responses:
            response.save()
        self.edit.refresh()

    @staticmethod
    async def load(from_value: model.ExamTemplateQuestion) -> any:
        exam_template_id = (await from_value.exam_template.get()).id
        exam_template_question = ExamTemplateQuestion(
            id=from_value.id,
            exam_template_id=exam_template_id,
            type=from_value.type,
            body=from_value.body,
            responses=[],
        )
        responses: List[model.ExamTemplateQuestionResponse] = (
            await from_value.responses.all()
        )
        for response in responses:
            exam_template_question.responses.append(
                ExamTemplateQuestionResponse.load(response)
            )
        return exam_template_question

    @ui.refreshable
    async def create(self) -> None:
        new_response = ExamTemplateQuestionResponse(
            id=None, exam_template_question_id=None, value=""
        )
        with ui.row():
            ui.select(
                options={t.value: t.name for t in model.QuestionType}, label="Type"
            ).bind_value(self, "type")
            ui.editor(placeholder="Question Body").bind_value(self, "body")
            with ui.column():
                with ui.row():
                    await new_response.create()
                for response in reversed(self.responses):
                    await response.edit()
            ui.button(on_click=self.new, icon="save").props("flat")

    @ui.refreshable
    async def edit(self) -> None:
        new_response = ExamTemplateQuestionResponse(
            id=None, exam_template_question_id=self.id, value=""
        )
        with ui.row():
            ui.select(
                options={t.value: t.name for t in model.QuestionType}, label="Type"
            ).bind_value(self, "type")
            ui.editor(placeholder="Question Body").bind_value(self, "body")
            with ui.column():
                await new_response.create()
                for response in reversed(self.responses):
                    await response.edit()
                    ui.button(
                        on_click=lambda: self.responses.remove(response), icon="delete"
                    ).props("flat")


@dataclass
class ExamTemplate(Serializable):

    id: UUID
    name: str
    questions: List[ExamTemplateQuestion] = field(default_factory=lambda: [])

    async def new(self) -> None:
        exam_template = await model.ExamTemplate.create(name=self.name)
        self.id = exam_template.id
        self.create.refresh()
        ui.navigate.to(f"/admin/exam/template/{exam_template.id}")

    async def save(self) -> None:
        await model.ExamTemplate.update_or_create(id=self.id, name=self.name)
        for question in self.questions:
            question.save()
        self.edit.refresh()

    @staticmethod
    async def load(from_value: model.ExamTemplate) -> any:
        exam_template = ExamTemplate(id=from_value.id, name=from_value.name)
        questions: List[model.ExamTemplateQuestion] = await from_value.questions.all()
        for question in questions:
            exam_template.questions.append(await ExamTemplateQuestion.load(question))
        return exam_template

    @ui.refreshable
    async def create(self) -> None:
        with ui.card():
            with ui.row():
                ui.input(label="Name").bind_value(self, "name")
                ui.button(on_click=self.new, icon="add").props("flat")

    @ui.refreshable
    async def edit(self) -> None:
        new_question = ExamTemplateQuestion(
            id=None, exam_template_id=self.id, type=None, body=""
        )
        with ui.card():
            with ui.row():
                ui.input("Exam Name").bind_value(self, "name")
                with ui.card_section():
                    ui.label("Exam Questions")
                    with ui.row():
                        await new_question.create()
                    for question in self.questions:
                        with ui.row():
                            await question.edit()
                ui.button(on_click=self.save, icon="save").props("flat")
