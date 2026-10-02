from django.contrib.auth.hashers import make_password
from django.test import TestCase

from accounts.models import User

from .models import Workspace


class WorkSpaceModelTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email="owner@gmail.com")  # pyright: ignore[reportCallIssue]

    def test_check_password_false_when_no_password_set(self):
        workspace = Workspace.objects.create(owner=self.owner, name="WorkSpace1")
        self.assertFalse(workspace.check_password("anything"))

    def test_check_password_true_for_correct_password(self):
        workspace = Workspace.objects.create(
            owner=self.owner, name="WorkSpace1", password=make_password("secret")
        )
        self.assertTrue(workspace.check_password("secret"))
        self.assertFalse(workspace.check_password("wrong"))
