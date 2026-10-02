from django.test import TestCase

from accounts.models import User
from workspaces.models import Workspace

from .models import Question, Survey


class SurveyModelTests(TestCase):
    def setUp(self):
        owner = User.objects.create_user(email="owner@gmail.com")  # pyright: ignore[reportCallIssue]
        self.workspace = Workspace.objects.create(owner=owner, name="W1")

    def test_default_status_is_draft(self):
        survey = Survey.objects.create(workspace=self.workspace, title="S1")
        self.assertEqual(survey.status, Survey.SurveyStatus.DRAFT)


class QuestionModelTests(TestCase):
    def setUp(self):
        owner = User.objects.create_user(email="owner@gmail.com")  # pyright: ignore[reportCallIssue]
        workspace = Workspace.objects.create(owner=owner, name="W1")
        self.survey = Survey.objects.create(workspace=workspace, title="S1")

    def test_defaults(self):
        question = Question.objects.create(survey=self.survey, title="Q1")
        self.assertEqual(question.type, Question.QuestionType.TEXT)
        self.assertFalse(question.is_required)
        self.assertEqual(question.order, 0)
        self.assertEqual(question.properties, {})
