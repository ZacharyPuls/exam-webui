from tortoise import fields, models
from tortoise.exceptions import NoValuesFetched


from enum import IntEnum


class User(models.Model):
    id = fields.UUIDField(pk=True)
    name = fields.TextField()
    email = fields.TextField()
    exams: fields.ReverseRelation["Exam"]


class Exam(models.Model):
    id = fields.UUIDField(pk=True)
    user = fields.ForeignKeyField(
        model_name="model.User", on_delete=fields.CASCADE, related_name="exams"
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
    exam = fields.ForeignKeyField(
        model_name="model.Exam", on_delete=fields.CASCADE, related_name="questions"
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
    exam_question = fields.ForeignKeyField(
        model_name="model.ExamQuestion",
        on_delete=fields.CASCADE,
        related_name="response",
    )
    submitted_datetime = fields.DatetimeField(auto_now=True)
    is_submitted = fields.BooleanField()


class ExamTemplate(models.Model):
    id = fields.UUIDField(pk=True)
    name = fields.TextField()
    questions: fields.ReverseRelation["ExamTemplateQuestion"]

    def num_questions(self) -> int:
        try:
            return len(self.questions)
        except NoValuesFetched:
            return 0


class ExamTemplateQuestion(models.Model):
    id = fields.UUIDField(pk=True)
    exam_template: fields.ForeignKeyRelation[ExamTemplate] = fields.ForeignKeyField(
        model_name="model.ExamTemplate",
        on_delete=fields.CASCADE,
        related_name="questions",
    )
    type = fields.IntEnumField(enum_type=QuestionType)
    body = fields.TextField()
