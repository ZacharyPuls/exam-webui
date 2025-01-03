from enum import IntEnum

from tortoise import fields, models
from tortoise.exceptions import NoValuesFetched


class User(models.Model):
    id = fields.UUIDField(pk=True)
    name = fields.TextField()
    email = fields.TextField()
    exams: fields.ReverseRelation["Exam"]


class Exam(models.Model):
    id = fields.UUIDField(pk=True)
    user: fields.ForeignKeyRelation[User] = fields.ForeignKeyField(
        model_name="model.User", related_name="exams"
    )
    name = fields.TextField()
    questions: fields.ReverseRelation["ExamQuestion"]
    is_complete = fields.BooleanField()

    def num_questions(self) -> int:
        try:
            return len(self.questions)
        except NoValuesFetched:
            return -1


class QuestionType(IntEnum):
    MULTIPLE_CHOICE_SINGLE_SELECT = 1
    MULTIPLE_CHOICE_MULTIPLE_SELECT = 2
    DRAG_AND_DROP_ORDERED = 3


class ExamQuestion(models.Model):
    id = fields.UUIDField(pk=True)
    exam: fields.ForeignKeyRelation[Exam] = fields.ForeignKeyField(
        model_name="model.Exam", related_name="questions"
    )
    type: QuestionType = fields.IntEnumField(enum_type=QuestionType)
    body = fields.TextField()
    response: fields.ReverseRelation["ExamQuestionResponse"]

    def is_complete(self) -> bool:
        try:
            return self.response is not None and len(self.response) > 0
        except NoValuesFetched:
            return False


class ExamQuestionResponse(models.Model):
    id = fields.UUIDField(pk=True)
    exam_question: fields.ForeignKeyRelation[ExamQuestion] = fields.ForeignKeyField(
        model_name="model.ExamQuestion", related_name="response"
    )
    submitted_datetime = fields.DatetimeField(auto_now=True)
    is_submitted = fields.BooleanField()


class ExamTemplate(models.Model):
    id = fields.UUIDField(pk=True)
    name = fields.TextField()
    created = fields.DatetimeField(auto_now_add=True)
    updated = fields.DatetimeField(auto_now=True)

    author: fields.ForeignKeyRelation[User] = fields.ForeignKeyField(
        model_name="model.User", related_name="authored_exam_templates"
    )
    updated_by: fields.ForeignKeyRelation[User] = fields.ForeignKeyField(
        model_name="model.User", related_name="updated_exam_templates"
    )
    questions: fields.ReverseRelation["ExamTemplateQuestion"]

    def num_questions(self) -> int:
        try:
            return len(self.questions)
        except NoValuesFetched:
            return 0


class ExamTemplateQuestion(models.Model):
    id = fields.UUIDField(pk=True)
    exam_template: fields.ForeignKeyRelation[ExamTemplate] = fields.ForeignKeyField(
        model_name="model.ExamTemplate", related_name="questions"
    )
    type = fields.IntEnumField(enum_type=QuestionType)
    body = fields.TextField()
    responses: fields.ReverseRelation["ExamTemplateQuestionResponse"]


class ExamTemplateQuestionResponse(models.Model):
    id = fields.UUIDField(pk=True)
    exam_template_question: fields.ForeignKeyRelation[ExamTemplateQuestion] = (
        fields.ForeignKeyField(
            model_name="model.ExamTemplateQuestion", related_name="responses"
        )
    )
    value = fields.TextField()
    is_correct = fields.BooleanField()
