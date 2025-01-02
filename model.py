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

    def __repr__(self):
        return str(
            f"ExamTemplate{{id={self.id}, name={self.name},questions=[{','.join([repr(question) for question in self.questions])}]}}"
        )


class ExamTemplateQuestion(models.Model):
    id = fields.UUIDField(pk=True)
    exam_template: fields.ForeignKeyRelation[ExamTemplate] = fields.ForeignKeyField(
        model_name="model.ExamTemplate",
        on_delete=fields.CASCADE,
        related_name="questions",
    )
    type = fields.IntEnumField(enum_type=QuestionType)
    body = fields.TextField()
    responses: fields.ReverseRelation["ExamTemplateQuestionResponse"]

    def __repr__(self):
        return str(
            f"ExamTemplateQuestion{{id={self.id}, exam_template={repr(self.exam_template.id)},type={self.type},body={self.body},responses=[{','.join([repr(response) for response in self.responses])}]}}"
        )


class ExamTemplateQuestionResponse(models.Model):
    id = fields.UUIDField(pk=True)
    exam_template_question: fields.ForeignKeyRelation[ExamTemplateQuestion] = (
        fields.ForeignKeyField(
            model_name="model.ExamTemplateQuestion",
            on_delete=fields.CASCADE,
            related_name="responses",
        )
    )
    value = fields.TextField()
    is_correct = fields.BooleanField()

    def __repr__(self):
        return str(
            f"ExamTemplateQuestionResponse{{id={self.id}, exam_template_question={repr(self.exam_template_question.id)},value={self.value},is_correct={self.is_correct}}}"
        )
