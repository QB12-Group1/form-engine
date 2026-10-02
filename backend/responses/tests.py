from django.test import TestCase

from accounts.models import User
from surveys.models import Survey
from workspaces.models import Workspace

from .models import ResponseSession


class ResponseSessionModelTests(TestCase):
    def setUp(self):
        owner = User.objects.create_user(email="owner@gmail.com")  # pyright: ignore[reportCallIssue]
        workspace = Workspace.objects.create(owner=owner, name="W1")
        self.survey = Survey.objects.create(workspace=workspace, title="S1")

    def test_defaults(self):
        session = ResponseSession.objects.create(
            survey=self.survey, respondent_ip="1.1.1.1", user_agent="test"
        )
        self.assertFalse(session.is_completed)
        self.assertIsNone(session.submitted_at)
